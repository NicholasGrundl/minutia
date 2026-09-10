"""Wizard flows — setup and guided-run — plus their pure cores.

Two flows drive the :mod:`.tui` primitives:

* **setup** — persist the recordings dir + the Anthropic API key into the user ``config.env`` (via
  :func:`minutia.config.write_user_config`), so the tool is ready after first run.
* **guided run** — pick a recording, choose a summary style, attach notes, confirm the cost, then
  run extract → transcribe → merge → summarize under the staged progress bar (the header telemetry
  reflects each stage), and end with an artifacts summary + a manual-cleanup nudge.

The *pure cores* (``RunPlan``, ``detect_env_api_key``) are separated from the drawing so they can be
unit-tested directly. The flows take an injected ``ui`` (defaulting to :mod:`.tui`) so tests drive
them with a fake terminal, and the heavy step functions are imported lazily inside the stage
closures (cold start stays cheap; the source modules are the patch seam for tests).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rich.text import Text

from ...config import USER_CONFIG_FILE, MinutiaSettings, write_user_config
from ...prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds
from .._steps import _read_optional_text, _resolve_notes_answer
from ..info import _list_recordings
from . import tui

# Env vars that carry the Anthropic key, in the settings layer's precedence order.
_API_KEY_VARS = ("ANTHROPIC_API_KEY", "MINUTIA_ANTHROPIC_API_KEY")
# The namespaced var we persist into the user config (read via the settings AliasChoices).
_PERSIST_KEY_VAR = "MINUTIA_ANTHROPIC_API_KEY"
_PERSIST_RECORDINGS_VAR = "MINUTIA_RECORDINGS_DIR"


# --- Pure cores ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class RunPlan:
    """The resolved plan for one guided run — everything needed to execute, no side effects."""

    recording: Path
    output_dir: Path
    prompt_kind: str
    notes_path: Path | None
    model_name: str


def detect_env_api_key(env: Mapping[str, str]) -> tuple[str, str] | None:
    """Return ``(var_name, value)`` for the first API-key env var set, else ``None``."""
    for var in _API_KEY_VARS:
        value = env.get(var)
        if value:
            return (var, value)
    return None


def _language_of(whisper_model: str) -> str:
    """The header's language tag from the whisper model (``medium.en`` → ``en``, else ``multi``)."""
    return "en" if whisper_model.endswith(".en") else "multi"


def _human_size(num_bytes: int) -> str:
    """A compact human-readable file size (e.g. ``412.6 MB``)."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _probe_duration(path: Path) -> str:
    """The recording's duration as ``M:SS`` via ffprobe, or ``—`` when it can't be read."""
    try:
        import ffmpeg

        seconds = int(float(ffmpeg.probe(str(path))["format"]["duration"]))
    except Exception:
        return "—"
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:d}:{secs:02d}"


def _recording_label(path: Path) -> str:
    """One picker row: name + modified date + size + duration, column-aligned."""
    stat = path.stat()
    date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    return (
        f"{path.name:<30}  {date}  {_human_size(stat.st_size):>9}  "
        f"{_probe_duration(path):>7}"
    )


# --- Setup flow ---------------------------------------------------------------------------------


def run_setup(
    config: MinutiaSettings,
    *,
    ui=tui,
    env: Mapping[str, str] | None = None,
    config_path: Path | None = None,
) -> bool:
    """Persist the recordings dir + API key into the user config. Returns False if cancelled."""
    env = os.environ if env is None else env
    config_path = USER_CONFIG_FILE if config_path is None else config_path
    updates: dict[str, str] = {}

    default_dir = config.recordings_dir or (Path.home() / "Videos")
    rec_options = [f"Use {default_dir}", "Paste a folder path", "Skip"]
    rec_choice = ui.select(
        [Text("Where do your recordings (.mkv files) live?", style="bold")], rec_options
    )
    if rec_choice is None:
        return False
    if rec_choice == 0:
        updates[_PERSIST_RECORDINGS_VAR] = str(Path(default_dir).expanduser())
    elif rec_choice == 1:
        answer = ui.prompt_text(
            [Text("Paste the recordings folder path", style="bold")],
            title="folder path",
        )
        if answer is None:
            return False
        if answer.strip():
            updates[_PERSIST_RECORDINGS_VAR] = str(Path(answer.strip()).expanduser())

    detected = detect_env_api_key(env)
    options = ["Paste an API key"]
    if detected is not None:
        options.append(f"Use {detected[0]} already in your environment")
    options.append("Skip for now")
    choice = ui.select([Text("Anthropic API key", style="bold")], options)
    if choice is None:
        return False
    picked = options[choice]
    if picked.startswith("Paste"):
        key = ui.prompt_text(
            [Text("Paste your Anthropic API key (it is stored locally, chmod 600)", style="bold")],
            title="sk-ant-…",
        )
        if key and key.strip():
            updates[_PERSIST_KEY_VAR] = key.strip()
    elif detected is not None and picked.startswith("Use"):
        updates[_PERSIST_KEY_VAR] = detected[1]

    if updates:
        path = write_user_config(updates, path=config_path)
        saved = ", ".join(sorted(updates))
        ui.console().print(f"Saved {saved} to {path}")
    else:
        ui.console().print("Nothing to save.")
    return True


# --- Guided-run flow ----------------------------------------------------------------------------


def _collect_notes(ui, output_dir: Path) -> tuple[bool, Path | None]:
    """Notes panel: paste multi-line / point at a file / none. Returns ``(ok, path)``."""
    options = ["Paste notes", "Use a notes file", "No notes"]
    choice = ui.select([Text("Meeting notes (speaker names, context…)", style="bold")], options)
    if choice is None:
        return (False, None)
    if choice == 0:
        text = ui.prompt_notes([Text("Notes", style="bold")])
        if text is None:
            return (False, None)
        return (True, _resolve_notes_answer(text, output_dir))
    if choice == 1:
        answer = ui.prompt_text([Text("Path to a notes file", style="bold")], title="notes.md")
        if answer is None:
            return (False, None)
        return (True, _resolve_notes_answer(answer, output_dir))
    return (True, None)


def _print_artifacts(ui, output_dir: Path, report: Path | None) -> None:
    """The end-of-run summary: what was produced + a manual-cleanup nudge (no archive command)."""
    console = ui.console()
    console.print(Text("\nArtifacts", style="bold"))
    console.print(f"  working dir      {output_dir}")
    console.print(f"  merged transcript {output_dir / 'merged_transcript.json'}")
    if report is not None:
        console.print(f"  report           {report}")
    console.print(
        Text(
            "\nWhen you are done, remove the .mkv and these outputs (or archive them "
            "per project) — minutia does not clean up for you.",
            style="dim",
        )
    )


def run_guided(config: MinutiaSettings, *, ui=tui) -> None:
    """The guided daily-driver run — pick, configure, confirm, process, summarize, report."""
    console = ui.console()
    if config.recordings_dir is None:
        console.print(
            "No recordings directory configured. Run `minutia setup` first."
        )
        return
    recordings_dir = Path(config.recordings_dir).expanduser()
    if not recordings_dir.is_dir():
        console.print(f"Recordings directory does not exist: {recordings_dir}")
        return
    recordings = _list_recordings(recordings_dir)
    if not recordings:
        console.print(f"No .mkv files found in {recordings_dir}")
        return

    pick = ui.select(
        [Text("Pick a recording  (name · modified · size · length)", style="bold")],
        [_recording_label(p) for p in recordings],
    )
    if pick is None:
        return
    recording = recordings[pick]

    kinds = list_prompt_kinds()
    kind_choice = ui.select(
        [Text("Summary style", style="bold")],
        kinds,
        cursor_index=kinds.index(DEFAULT_PROMPT_KIND),
    )
    if kind_choice is None:
        return
    prompt_kind = kinds[kind_choice]

    output_dir = config.base_output_dir / recording.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    ok, notes_path = _collect_notes(ui, output_dir)
    if not ok:
        return

    plan = RunPlan(
        recording=recording,
        output_dir=output_dir,
        prompt_kind=prompt_kind,
        notes_path=notes_path,
        model_name=config.summary_model,
    )

    status = ui.HeaderStatus(language=_language_of(config.whisper_model))
    merged_path = output_dir / "merged_transcript.json"
    ctx: dict[str, dict[str, str]] = {}

    def do_extract() -> None:
        from ...steps.video_extraction import process_mkv_file

        ctx["audio"] = process_mkv_file(
            str(plan.recording),
            str(plan.output_dir),
            mic_track_number=config.mic_track,
            desktop_track_number=config.desktop_track,
        )

    def do_transcribe() -> None:
        from ...steps.audio_transcription import process_audio_files

        ctx["transcripts"] = process_audio_files(
            str(plan.output_dir / "microphone_audio.wav"),
            str(plan.output_dir / "desktop_audio.wav"),
            str(plan.output_dir),
            whisper_model_name=config.whisper_model,
            use_gpu=True,
        )

    def do_merge() -> None:
        from ...steps.transcript_merger import process_transcripts

        transcripts = ctx["transcripts"]
        process_transcripts(
            str(transcripts["microphone"]),
            str(transcripts["desktop"]),
            str(merged_path),
        )

    stage_results = ui.run_staged_progress(
        [
            ui.Step(0.25, "extracting audio", do_extract, state="extract"),
            ui.Step(0.6, "transcribing", do_transcribe, state="transcribe"),
            ui.Step(0.8, "merging transcripts", do_merge, state="merge"),
        ],
        [Text(f"Recording: {recording.name}")],
        status=status,
    )
    failure = next((r for r in stage_results if isinstance(r, tui.StepError)), None)
    if failure is not None:
        console.print(f"\n{failure.label} failed: {failure.message}")
        _print_artifacts(ui, output_dir, report=None)
        return

    from ...steps.summarize_transcript import (
        estimate_tokens_and_price,
        extract_transcript_text,
        load_transcript,
    )

    transcript_text = extract_transcript_text(load_transcript(str(merged_path)))
    tokens, price = estimate_tokens_and_price(transcript_text, plan.model_name)
    confirm = ui.select(
        [
            Text(
                f"Estimated {tokens:,} tokens · ${price:.4f} · model {plan.model_name}",
                style="bold",
            )
        ],
        ["Summarize now", "Stop here (keep transcript)"],
    )
    if confirm != 0:
        _print_artifacts(ui, output_dir, report=None)
        return

    if not config.anthropic_api_key:
        console.print("No Anthropic API key configured. Run `minutia setup` first.")
        _print_artifacts(ui, output_dir, report=None)
        return
    api_key = config.anthropic_api_key  # narrowed to str for the summarize calls

    def do_summarize() -> Path:
        from ...prompts import generate_meeting_summary_prompt
        from ...steps.summarize_transcript import (
            create_markdown_report,
            generate_long_summary,
        )

        notes_text = _read_optional_text(plan.notes_path, "Notes")
        personal_info = _read_optional_text(config.personal_info_path, "Personal info")
        system_prompt = generate_meeting_summary_prompt(
            notes_text, personal_info, kind=plan.prompt_kind
        )
        summary = generate_long_summary(
            transcript_text,
            model_name=plan.model_name,
            system_prompt=system_prompt,
            api_key=api_key,
        )
        return create_markdown_report(
            summary,
            plan.output_dir,
            model_name=plan.model_name,
            api_key=api_key,
        )

    (report,) = ui.run_staged_progress(
        [ui.Step(0.95, "summarizing", do_summarize, state="summarize")],
        [Text(f"Recording: {recording.name}")],
        status=status,
    )
    if isinstance(report, tui.StepError):
        console.print(f"\nSummarize failed: {report.message}")
        _print_artifacts(ui, output_dir, report=None)
        return
    _print_artifacts(ui, output_dir, report)
