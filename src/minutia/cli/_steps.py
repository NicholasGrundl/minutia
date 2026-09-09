"""Shared pipeline-step helpers for the CLI.

These are the reusable building blocks that both the current commands (in ``app.py``) and the
future ``run`` group / guided-run wizard execute against. They wrap the ``steps/`` modules with the
CLI's skip-when-outputs-exist behavior, cost confirmation, and friendly errors.

Cold-start discipline: the heavy step modules (torch/whisper via ``audio_transcription``, anthropic
via ``summarize_transcript``, ffmpeg via ``video_extraction``) are imported **lazily, inside the
functions that run them** — never at module load. Importing this module (and therefore the whole
``minutia.cli`` package, which happens for ``--help`` / ``--version`` / ``config``) stays cheap.

Tests that need to stub a step function patch it **at its source module** (e.g.
``minutia.steps.audio_transcription.process_audio_files``), which is where the lazy import looks it
up at call time.
"""

from pathlib import Path

import click
import typer

from ..config import ConfigurationError, MinutiaSettings
from ..paths import resolve_input_video
from ..prompts import generate_meeting_summary_prompt


def _resolve_input_or_fail(config: MinutiaSettings, input_video: Path | None) -> Path:
    """Resolve the input MKV (explicit or newest recording), echoing discovery."""
    try:
        resolved = resolve_input_video(input_video, config.recordings_dir)
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    if input_video is None:
        typer.echo(f"No input given — using newest recording: {resolved}")
    return resolved


def _read_optional_text(path: Path | None, label: str) -> str:
    """Read an optional context file, failing with a friendly error."""
    if path is None:
        return ""
    path = path.expanduser()
    if not path.exists():
        raise click.ClickException(f"{label} file not found: {path}")
    return path.read_text(encoding="utf-8")


def _resolve_notes_answer(answer: str, output_dir: Path) -> Path | None:
    """Resolve the guided `go` notes answer, which may be a path *or* inline text.

    - blank            -> no notes
    - an existing file -> use it as-is
    - anything else     -> treat as inline notes, persisted to <output_dir>/notes.md
      so the text reaches the summarizer and stays alongside the run artifacts.
    """
    answer = answer.strip()
    if not answer:
        return None
    candidate = Path(answer).expanduser()
    if candidate.is_file():
        return candidate
    notes_file = output_dir / "notes.md"
    notes_file.write_text(answer + "\n", encoding="utf-8")
    typer.echo(f"Saved inline notes to: {notes_file}")
    return notes_file


def _extract_audio_step(
    config: MinutiaSettings,
    input_video: Path,
    output_dir: Path,
    mic_track: int | None,
    desktop_track: int | None,
    force: bool,
) -> None:
    """Extract audio tracks, skipping when both wavs already exist (mirrors notebook)."""
    expected = [output_dir / "microphone_audio.wav", output_dir / "desktop_audio.wav"]
    if not force and all(p.exists() for p in expected):
        typer.echo("Audio files already exist, skipping extraction (--force to redo):")
        for p in expected:
            typer.echo(f"  {p}")
        return
    # Lazy: ffmpeg pulled in only when we actually extract (keeps cold start cheap).
    from ..steps.video_extraction import process_mkv_file

    mic_track = mic_track if mic_track is not None else config.mic_track
    desktop_track = desktop_track if desktop_track is not None else config.desktop_track
    audio_files = process_mkv_file(
        str(input_video),
        str(output_dir),
        mic_track_number=mic_track,
        desktop_track_number=desktop_track,
    )
    typer.echo(f"Audio files extracted: {audio_files}")


def _transcribe_step(
    config: MinutiaSettings,
    mic_audio: Path,
    desktop_audio: Path,
    output_dir: Path,
    whisper_model: str | None,
    gpu: bool,
    force: bool,
) -> dict[str, Path]:
    """Transcribe both tracks, skipping when the transcription JSONs already exist."""
    model_name = whisper_model or config.whisper_model
    expected = {
        kind: output_dir / f"{kind}-whisper-{model_name}_transcription.json"
        for kind in ("microphone", "desktop")
    }
    if not force and all(p.exists() for p in expected.values()):
        typer.echo("Transcriptions already exist, skipping (--force to re-transcribe):")
        for p in expected.values():
            typer.echo(f"  {p}")
        return expected
    # Lazy: torch/whisper pulled in only when we actually transcribe.
    from ..steps.audio_transcription import process_audio_files

    transcriptions = process_audio_files(
        str(mic_audio),
        str(desktop_audio),
        str(output_dir),
        whisper_model_name=model_name,
        use_gpu=gpu,
    )
    typer.echo(f"Transcriptions created: {transcriptions}")
    return {kind: Path(path) for kind, path in transcriptions.items()}


def _summarize_step(
    config: MinutiaSettings,
    merged_transcript: Path,
    output_dir: Path,
    prompt_kind: str,
    notes_path: Path | None,
    personal_info_path: Path | None,
    model_name: str,
    dry_run: bool,
    yes: bool,
) -> Path | None:
    """Estimate cost, confirm, generate the long summary, write the markdown report."""
    # Lazy: anthropic/tiktoken pulled in only when we actually summarize.
    from ..steps.summarize_transcript import (
        create_markdown_report,
        estimate_tokens_and_price,
        extract_transcript_text,
        generate_long_summary,
        load_transcript,
    )

    markdown_notes = _read_optional_text(notes_path, "Notes")
    personal_info = _read_optional_text(
        personal_info_path or config.personal_info_path, "Personal info"
    )

    transcript_data = load_transcript(str(merged_transcript))
    transcript_text = extract_transcript_text(transcript_data)

    total_tokens, estimated_price = estimate_tokens_and_price(
        transcript_text, model_name
    )
    typer.echo(f"Prompt kind: {prompt_kind} | model: {model_name}")
    typer.echo(
        f"Estimated tokens: {total_tokens:,} | estimated price: ${estimated_price:.4f}"
    )
    if dry_run:
        typer.echo("Dry run completed. No summary generated.")
        return None
    if not yes:
        typer.confirm("Proceed with summarization?", abort=True)

    if not config.anthropic_api_key:
        raise click.ClickException(
            "Anthropic API key not configured. Set ANTHROPIC_API_KEY or MINUTIA_ANTHROPIC_API_KEY."
        )

    system_prompt = generate_meeting_summary_prompt(
        markdown_notes, personal_info, kind=prompt_kind
    )
    summary = generate_long_summary(
        transcript_text,
        model_name=model_name,
        system_prompt=system_prompt,
        api_key=config.anthropic_api_key,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = create_markdown_report(
        summary,
        output_dir,
        model_name=model_name,
        api_key=config.anthropic_api_key,
    )
    typer.echo(f"Markdown report saved to: {report_path}")
    return report_path
