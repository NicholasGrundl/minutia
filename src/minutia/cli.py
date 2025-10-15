from collections.abc import Iterable
from pathlib import Path

import click

from .audio_transcription import process_audio_files
from .config import ConfigurationError, MinutiaConfig, load_config
from .logging import configure_logging, logger
from .paths import RunPaths
from .pipeline import PipelineConfig, PipelineOrchestrator, PipelineResult, StepStatus
from .summarize_transcript import (
    estimate_tokens_and_price,
    generate_summary,
    load_transcript,
    prepare_transcript_for_summary,
    save_summary,
)
from .transcript_merger import process_transcripts
from .video_extraction import process_mkv_file


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    """OBS Video Processing CLI"""
    try:
        config = load_config()
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    configure_logging(level=config.log_level)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    logger.info(
        "CLI initialised with whisper_model={}, summary_model={}, output_dir={}, anthropic_key={}",
        config.whisper_model,
        config.summary_model,
        config.base_output_dir,
        config.masked_anthropic_key,
    )


@cli.command()
@click.pass_context
@click.argument("input_video", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path(), required=False)
@click.option(
    "--mic-track",
    type=int,
    default=None,
    help="Track number for microphone audio (defaults to configuration)",
)
@click.option(
    "--desktop-track",
    type=int,
    default=None,
    help="Track number for desktop audio (defaults to configuration)",
)
def extract_audio(ctx, input_video, output_dir, mic_track, desktop_track):
    """Extract audio tracks from MKV file."""
    config = ctx.obj["config"]
    mic_track = mic_track if mic_track is not None else config.mic_track
    desktop_track = desktop_track if desktop_track is not None else config.desktop_track
    output_directory = Path(output_dir).expanduser() if output_dir else config.base_output_dir
    try:
        audio_files = process_mkv_file(
            input_video,
            str(output_directory),
            mic_track_number=mic_track,
            desktop_track_number=desktop_track,
        )
        click.echo(f"Audio files extracted: {audio_files}")
    except Exception as e:
        logger.exception("Audio extraction failed: {}", e)
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
@click.argument("mic_audio", type=click.Path(exists=True))
@click.argument("desktop_audio", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path(), required=False)
def transcribe(ctx, mic_audio, desktop_audio, output_dir):
    """Transcribe audio files."""
    config = ctx.obj["config"]
    output_directory = Path(output_dir).expanduser() if output_dir else config.base_output_dir
    try:
        transcriptions = process_audio_files(mic_audio, desktop_audio, str(output_directory))
        click.echo(f"Transcriptions created: {transcriptions}")
    except Exception as e:
        logger.exception("Transcription failed: {}", e)
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
@click.argument("mic_transcript", type=click.Path(exists=True))
@click.argument("desktop_transcript", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
def merge_transcripts(ctx, mic_transcript, desktop_transcript, output_file):
    """Merge microphone and desktop transcripts."""
    try:
        process_transcripts(mic_transcript, desktop_transcript, output_file)
        click.echo(f"Merged transcript saved to: {output_file}")
    except Exception as e:
        logger.exception("Transcript merging failed: {}", e)
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
@click.argument("merged_transcript", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option(
    "--model",
    type=click.Choice(["claude-4-5-sonnet", "claude-3-5-sonnet", "claude-3-haiku"]),
    default=None,
    help="Model to use for summarization (defaults to configuration)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Estimate tokens and price without generating summary",
)
def summarize(ctx, merged_transcript, output_file, model, dry_run):
    """Generate summary from merged transcript."""
    config = ctx.obj["config"]
    model_name = model or config.summary_model
    try:
        transcript_data = load_transcript(merged_transcript)
        transcript_text = prepare_transcript_for_summary(transcript_data)

        total_tokens, estimated_price = estimate_tokens_and_price(
            transcript_text, model_name
        )
        click.echo(f"Estimated tokens: {total_tokens}")
        click.echo(f"Estimated price: ${estimated_price:.4f}")

        if dry_run:
            click.echo("Dry run completed. No summary generated.")
            return

        if not config.anthropic_api_key:
            raise click.ClickException(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY or MINUTIA_ANTHROPIC_API_KEY."
            )

        summary = generate_summary(
            transcript_text,
            model_name=model_name,
            api_key=config.anthropic_api_key,
        )
        save_summary(summary, output_file)
        click.echo(f"Summary saved to: {output_file}")
    except Exception as e:
        logger.exception("Summary generation failed: {}", e)
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
@click.argument("input_video", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path(), required=False)
@click.option(
    "--mic-track",
    type=int,
    default=None,
    help="Track number for microphone audio (defaults to configuration)",
)
@click.option(
    "--desktop-track",
    type=int,
    default=None,
    help="Track number for desktop audio (defaults to configuration)",
)
@click.option(
    "--model",
    type=click.Choice(["claude-4-5-sonnet", "claude-3-5-sonnet", "claude-3-haiku"]),
    default=None,
    help="Model to use for summarization (defaults to configuration)",
)
def process_all(ctx, input_video, output_dir, mic_track, desktop_track, model):
    """Run the entire video processing workflow."""
    config = ctx.obj["config"]
    model_name = model or config.summary_model
    mic_track = mic_track if mic_track is not None else config.mic_track
    desktop_track = desktop_track if desktop_track is not None else config.desktop_track
    output_directory = _resolve_output_dir(config, output_dir)

    pipeline_config = _build_pipeline_config(
        cli_config=config,
        input_video=input_video,
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


def _resolve_output_dir(config: MinutiaConfig, output_dir: str | None) -> Path:
    """Return the output directory for the run respecting CLI overrides."""
    if output_dir:
        return Path(output_dir).expanduser()
    return config.base_output_dir


def _build_pipeline_config(
    *,
    cli_config: MinutiaConfig,
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
    )


def _render_progress(progress) -> None:
    """Display lightweight progress information for pipeline steps."""
    status_label = progress.status.value.upper()
    message = progress.message or ""
    if progress.status is StepStatus.RUNNING:
        click.echo(f"[{status_label}] {progress.step_name}: {message or 'Starting...'}")
        return
    if progress.status is StepStatus.COMPLETED:
        click.echo(f"[{status_label}] {progress.step_name}: {message or 'Completed'}")
        return
    if progress.status is StepStatus.FAILED:
        error_text = str(progress.error or message or "Step failed")
        click.echo(f"[{status_label}] {progress.step_name}: {error_text}")


def _render_success_message(result: PipelineResult) -> None:
    """Emit user-facing summary of pipeline outputs."""
    click.echo("Pipeline completed successfully.")
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
        click.echo(f"  {label}: {path}")


def _format_failure_message(result: PipelineResult) -> str:
    """Create a friendly error message for failed pipeline runs."""
    failed_step = result.failed_step or "unknown step"
    error_message = str(result.error or "Unknown error")
    logs_hint = f" See logs at {result.run_paths.logs_file}" if result.run_paths.logs_file else ""
    return f"Pipeline failed during '{failed_step}': {error_message}.{logs_hint}"


if __name__ == "__main__":
    cli()
