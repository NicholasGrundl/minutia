from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Annotated

import click
import typer

from .config import (
    USER_CONFIG_FILE,
    ConfigurationError,
    MinutiaSettings,
    resolve_settings,
)
from .logging import configure_logging, logger
from .model_registry import anthropic_models
from .paths import RunPaths, resolve_input_video
from .pipeline.orchestrator import (
    PipelineConfig,
    PipelineOrchestrator,
    PipelineResult,
    StepStatus,
)
from .prompts import (
    DEFAULT_PROMPT_KIND,
    generate_meeting_summary_prompt,
    list_prompt_kinds,
)
from .steps.audio_transcription import process_audio_files
from .steps.summarize_transcript import (
    create_markdown_report,
    estimate_tokens_and_price,
    extract_transcript_text,
    generate_long_summary,
    load_transcript,
)
from .steps.transcript_merger import process_transcripts
from .steps.video_extraction import process_mkv_file

# Enums drive typer's CLI choices (click.Choice equivalent); both derive from
# their single source of truth so the CLI can never drift from validation.
SummaryModel = Enum(
    "SummaryModel", {choice: choice for choice in anthropic_models}, type=str
)
PromptKind = Enum("PromptKind", {kind: kind for kind in list_prompt_kinds()}, type=str)

app = typer.Typer(
    name="minutia",
    help="OBS Video Processing CLI",
    add_completion=False,
)

MicTrackOption = Annotated[
    int | None,
    typer.Option(help="Track number for microphone audio (defaults to configuration)"),
]
DesktopTrackOption = Annotated[
    int | None,
    typer.Option(help="Track number for desktop audio (defaults to configuration)"),
]
SummaryModelOption = Annotated[
    SummaryModel | None,
    typer.Option(help="Model to use for summarization (defaults to configuration)"),
]
ForceOption = Annotated[
    bool, typer.Option("--force", help="Redo the work even if outputs already exist")
]
EnvFileOption = Annotated[
    Path | None,
    typer.Option(
        "--env-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Use this contextual .env file instead of automatic discovery",
    ),
]
NoEnvFileOption = Annotated[
    bool,
    typer.Option(
        "--no-env-file",
        help="Disable contextual .env discovery (the user config still loads)",
    ),
]


@app.callback()
def main_callback(
    ctx: typer.Context,
    env_file: EnvFileOption = None,
    no_env_file: NoEnvFileOption = False,
):
    """OBS Video Processing CLI"""
    if env_file is not None and no_env_file:
        raise click.ClickException(
            "--env-file and --no-env-file cannot be used together"
        )
    try:
        resolution = resolve_settings(
            env_file=env_file,
            discover_dotenv=not no_env_file,
        )
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    config = resolution.settings
    configure_logging(level=config.log_level)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["settings_resolution"] = resolution
    logger.info(
        "CLI initialised with whisper_model={}, summary_model={}, output_dir={}, anthropic_key={}",
        config.whisper_model,
        config.summary_model,
        config.base_output_dir,
        config.masked_anthropic_key,
    )


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


@app.command()
def extract_audio(
    ctx: typer.Context,
    input_video: Annotated[Path | None, typer.Argument(exists=True)] = None,
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    mic_track: MicTrackOption = None,
    desktop_track: DesktopTrackOption = None,
    force: ForceOption = False,
):
    """Extract audio tracks from MKV file (newest recording when no input given)."""
    config = ctx.obj["config"]
    input_video = _resolve_input_or_fail(config, input_video)
    output_directory = output_dir.expanduser() if output_dir else config.base_output_dir
    try:
        _extract_audio_step(
            config, input_video, output_directory, mic_track, desktop_track, force
        )
    except click.ClickException:
        raise
    except Exception as e:
        logger.exception("Audio extraction failed: {}", e)
        raise click.ClickException(str(e)) from e


@app.command()
def transcribe(
    ctx: typer.Context,
    mic_audio: Annotated[Path, typer.Argument(exists=True)],
    desktop_audio: Annotated[Path, typer.Argument(exists=True)],
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    whisper_model: Annotated[
        str | None,
        typer.Option(help="Whisper model name (defaults to configuration)"),
    ] = None,
    gpu: Annotated[
        bool, typer.Option("--gpu/--no-gpu", help="Use GPU acceleration if available")
    ] = True,
    force: ForceOption = False,
):
    """Transcribe audio files."""
    config = ctx.obj["config"]
    output_directory = output_dir.expanduser() if output_dir else config.base_output_dir
    try:
        _transcribe_step(
            config,
            mic_audio,
            desktop_audio,
            output_directory,
            whisper_model,
            gpu,
            force,
        )
    except click.ClickException:
        raise
    except Exception as e:
        logger.exception("Transcription failed: {}", e)
        raise click.ClickException(str(e)) from e


@app.command()
def merge_transcripts(
    ctx: typer.Context,
    mic_transcript: Annotated[Path, typer.Argument(exists=True)],
    desktop_transcript: Annotated[Path, typer.Argument(exists=True)],
    output_file: Annotated[Path, typer.Argument()],
):
    """Merge microphone and desktop transcripts."""
    try:
        process_transcripts(
            str(mic_transcript), str(desktop_transcript), str(output_file)
        )
        typer.echo(f"Merged transcript saved to: {output_file}")
    except Exception as e:
        logger.exception("Transcript merging failed: {}", e)
        raise click.ClickException(str(e)) from e


@app.command()
def summarize(
    ctx: typer.Context,
    merged_transcript: Annotated[Path, typer.Argument(exists=True)],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            help="Where the markdown report is written (default: next to the transcript)"
        ),
    ] = None,
    prompt_kind: Annotated[
        PromptKind,
        typer.Option("--prompt-kind", help="Which summary prompt flavor to use"),
    ] = PromptKind(DEFAULT_PROMPT_KIND),
    notes: Annotated[
        Path | None,
        typer.Option("--notes", help="Per-meeting notes/speaker-mapping markdown file"),
    ] = None,
    personal_info: Annotated[
        Path | None,
        typer.Option(
            "--personal-info",
            help="Personal-info file for the prompt (defaults to configuration)",
        ),
    ] = None,
    model: SummaryModelOption = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Estimate tokens and price without generating summary"
        ),
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the cost confirmation prompt")
    ] = False,
):
    """Generate an AI-named markdown meeting report from a merged transcript."""
    config = ctx.obj["config"]
    model_name = model.value if model else config.summary_model
    output_directory = (
        output_dir.expanduser() if output_dir else merged_transcript.parent
    )
    try:
        _summarize_step(
            config,
            merged_transcript,
            output_directory,
            prompt_kind.value,
            notes,
            personal_info,
            model_name,
            dry_run,
            yes,
        )
    except (click.ClickException, click.exceptions.Abort):
        raise
    except Exception as e:
        logger.exception("Summary generation failed: {}", e)
        raise click.ClickException(str(e)) from e


@app.command()
def process_all(
    ctx: typer.Context,
    input_video: Annotated[Path | None, typer.Argument(exists=True)] = None,
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    mic_track: MicTrackOption = None,
    desktop_track: DesktopTrackOption = None,
    model: SummaryModelOption = None,
):
    """Run the entire video processing workflow (newest recording when no input given)."""
    config = ctx.obj["config"]
    input_video = _resolve_input_or_fail(config, input_video)
    model_name = model.value if model else config.summary_model
    mic_track = mic_track if mic_track is not None else config.mic_track
    desktop_track = desktop_track if desktop_track is not None else config.desktop_track
    output_directory = _resolve_output_dir(config, output_dir)

    pipeline_config = _build_pipeline_config(
        cli_config=config,
        input_video=str(input_video),
        output_directory=output_directory,
        mic_track=mic_track,
        desktop_track=desktop_track,
        summary_model=model_name,
    )

    try:
        orchestrator = PipelineOrchestrator(progress_callback=_render_progress)
        result = orchestrator.execute(pipeline_config)
    except Exception as exc:  # noqa: BLE001 - surface human readable error
        logger.exception("Pipeline orchestration failed: {}", exc)
        raise click.ClickException(f"Pipeline execution failed: {exc}") from exc

    if not result.success:
        error_message = _format_failure_message(result)
        logger.error(error_message)
        raise click.ClickException(error_message)

    _render_success_message(result)


@app.command()
def go(
    ctx: typer.Context,
    recordings_path: Annotated[
        Path | None,
        typer.Argument(
            exists=True,
            file_okay=False,
            help="Directory to browse for .mkv files (default: configured recordings dir)",
        ),
    ] = None,
    force: ForceOption = False,
):
    """Guided run: pick a recording, choose a prompt kind, confirm cost, get a report."""
    config: MinutiaSettings = ctx.obj["config"]

    if recordings_path is not None:
        recordings_dir = recordings_path.expanduser()
    elif config.recordings_dir is not None:
        recordings_dir = Path(config.recordings_dir).expanduser()
    else:
        raise click.ClickException(
            "No recordings directory configured. Pass a directory (e.g. `minutia go .`) "
            f"or set MINUTIA_RECORDINGS_DIR (e.g. in {USER_CONFIG_FILE})."
        )
    if not recordings_dir.is_dir():
        raise click.ClickException(
            f"Recordings directory does not exist: {recordings_dir}"
        )
    recordings = sorted(
        recordings_dir.glob("*.mkv"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not recordings:
        raise click.ClickException(f"No .mkv files found in {recordings_dir}")

    typer.echo("Recordings (newest first):")
    for index, path in enumerate(recordings[:10], start=1):
        typer.echo(f"  {index}. {path.name}")
    choice = typer.prompt("Which recording?", default=1, type=int)
    if not 1 <= choice <= min(len(recordings), 10):
        raise click.ClickException(
            f"Choice must be between 1 and {min(len(recordings), 10)}"
        )
    input_video = recordings[choice - 1]

    kinds = list_prompt_kinds()
    typer.echo("Prompt kinds:")
    for index, kind in enumerate(kinds, start=1):
        marker = " (default)" if kind == DEFAULT_PROMPT_KIND else ""
        typer.echo(f"  {index}. {kind}{marker}")
    kind_choice = typer.prompt(
        "Which prompt kind?", default=kinds.index(DEFAULT_PROMPT_KIND) + 1, type=int
    )
    if not 1 <= kind_choice <= len(kinds):
        raise click.ClickException(f"Choice must be between 1 and {len(kinds)}")
    prompt_kind = kinds[kind_choice - 1]

    notes_answer = typer.prompt(
        "Notes (text or a file path; blank for none)", default="", show_default=False
    ).strip()

    output_dir = config.base_output_dir / input_video.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Working in: {output_dir}")

    notes_path = _resolve_notes_answer(notes_answer, output_dir)

    try:
        _extract_audio_step(config, input_video, output_dir, None, None, force)
        transcripts = _transcribe_step(
            config,
            output_dir / "microphone_audio.wav",
            output_dir / "desktop_audio.wav",
            output_dir,
            None,
            True,
            force,
        )
        merged_path = output_dir / "merged_transcript.json"
        process_transcripts(
            str(transcripts["microphone"]),
            str(transcripts["desktop"]),
            str(merged_path),
        )
        typer.echo(f"Merged transcript saved to: {merged_path}")
        _summarize_step(
            config,
            merged_path,
            output_dir,
            prompt_kind,
            notes_path,
            None,
            config.summary_model,
            False,
            False,
        )
    except (click.ClickException, click.exceptions.Abort):
        raise
    except Exception as e:
        logger.exception("Guided run failed: {}", e)
        raise click.ClickException(str(e)) from e


@app.command("config")
def show_config(ctx: typer.Context):
    """Show resolved configuration values and where each came from."""
    resolution = ctx.obj["settings_resolution"]
    config: MinutiaSettings = resolution.settings
    rows: Iterable[tuple[str, object]] = (
        ("whisper_model", config.whisper_model),
        ("summary_model", config.summary_model),
        ("mic_track", config.mic_track),
        ("desktop_track", config.desktop_track),
        ("base_output_dir", config.base_output_dir),
        ("recordings_dir", config.recordings_dir),
        ("personal_info_path", config.personal_info_path),
        ("log_level", config.log_level),
        ("cleanup_policy", config.cleanup_policy.value),
        ("anthropic_api_key", config.masked_anthropic_key),
    )
    for name, value in rows:
        source = resolution.sources.get(name, "default")
        typer.echo(f"{name} = {value if value is not None else '<unset>'}  [{source}]")
    typer.echo(f"\ninvocation directory: {resolution.invocation_dir}")
    typer.echo(
        "contextual env file: "
        f"{resolution.context_env_file if resolution.context_env_file else '<none>'}"
    )
    typer.echo(f"user config file: {resolution.user_config_file}")
    typer.echo(
        "precedence: CLI flag > environment > contextual .env > user config > default"
    )


def _resolve_output_dir(config: MinutiaSettings, output_dir: Path | None) -> Path:
    """Return the output directory for the run respecting CLI overrides."""
    if output_dir:
        return output_dir.expanduser()
    return config.base_output_dir


def _build_pipeline_config(
    *,
    cli_config: MinutiaSettings,
    input_video: str,
    output_directory: Path,
    mic_track: int,
    desktop_track: int,
    summary_model: str,
) -> PipelineConfig:
    """Construct a PipelineConfig object from CLI parameters and configuration."""
    run_paths = RunPaths.from_video_input(input_video, base_output_dir=output_directory)
    return PipelineConfig(
        input_path=run_paths.input_path,
        run_paths=run_paths,
        run_id=run_paths.run_root.name,
        whisper_model=cli_config.whisper_model,
        skip_summary=False,
        summary_model=summary_model,
        mic_track=mic_track,
        desktop_track=desktop_track,
        base_output_dir=output_directory,
        anthropic_api_key=cli_config.anthropic_api_key,
        log_level=cli_config.log_level,
        cleanup_policy=cli_config.cleanup_policy,
    )


def _render_progress(progress) -> None:
    """Display lightweight progress information for pipeline steps."""
    status_label = progress.status.value.upper()
    message = progress.message or ""
    if progress.status is StepStatus.RUNNING:
        typer.echo(f"[{status_label}] {progress.step_name}: {message or 'Starting...'}")
        return
    if progress.status is StepStatus.COMPLETED:
        typer.echo(f"[{status_label}] {progress.step_name}: {message or 'Completed'}")
        return
    if progress.status is StepStatus.FAILED:
        error_text = str(progress.error or message or "Step failed")
        typer.echo(f"[{status_label}] {progress.step_name}: {error_text}")


def _render_success_message(result: PipelineResult) -> None:
    """Emit user-facing summary of pipeline outputs."""
    typer.echo("Pipeline completed successfully.")
    artifact_lines: Iterable[tuple[str, Path]] = (
        ("Run directory", result.run_paths.run_root),
        ("Audio directory", result.run_paths.audio_dir),
        ("Microphone audio", result.run_paths.microphone_audio),
        ("Desktop audio", result.run_paths.desktop_audio),
        ("Transcripts directory", result.run_paths.transcripts_dir),
        ("Merged transcript", result.run_paths.merged_transcript),
        ("Summary", result.run_paths.summary_file),
        ("Log file", result.run_paths.logs_file),
    )
    for label, path in artifact_lines:
        typer.echo(f"  {label}: {path}")


def _format_failure_message(result: PipelineResult) -> str:
    """Create a friendly error message for failed pipeline runs."""
    failed_step = result.failed_step or "unknown step"
    error_message = str(result.error or "Unknown error")
    logs_hint = (
        f" See logs at {result.run_paths.logs_file}"
        if result.run_paths.logs_file
        else ""
    )
    return f"Pipeline failed during '{failed_step}': {error_message}.{logs_hint}"


# Click-compatible command object: keeps the console-script entry point
# (minutia.cli:main), the package re-export, and click.testing.CliRunner working.
main = typer.main.get_command(app)

if __name__ == "__main__":
    main()
