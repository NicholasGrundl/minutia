import os
from pathlib import Path

import click

from .audio_transcription import process_audio_files
from .config import ConfigurationError, load_config
from .logging import configure_logging, logger
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
    output_directory = Path(output_dir).expanduser() if output_dir else config.base_output_dir

    try:
        # Step 1: Process MKV file
        click.echo("Step 1: Processing MKV file")
        audio_files = process_mkv_file(
            input_video,
            str(output_directory),
            mic_track_number=mic_track,
            desktop_track_number=desktop_track,
        )

        # Step 2: Transcribe audio files
        click.echo("Step 2: Transcribing audio files")
        transcriptions = process_audio_files(
            audio_files["microphone"],
            audio_files["desktop"],
            str(output_directory),
        )

        # Step 3: Merge transcripts
        click.echo("Step 3: Merging transcripts")
        merged_transcript_file = os.path.join(output_directory, "merged_transcript.json")
        process_transcripts(
            transcriptions["microphone"],
            transcriptions["desktop"],
            merged_transcript_file,
        )

        # Step 4: Generate summary
        click.echo("Step 4: Generating summary")
        transcript_data = load_transcript(merged_transcript_file)
        transcript_text = prepare_transcript_for_summary(transcript_data)

        total_tokens, estimated_price = estimate_tokens_and_price(
            transcript_text, model_name
        )
        click.echo(f"Estimated tokens for summary: {total_tokens}")
        click.echo(f"Estimated price for summary: ${estimated_price:.4f}")

        if not config.anthropic_api_key:
            raise click.ClickException(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY or MINUTIA_ANTHROPIC_API_KEY."
            )

        summary = generate_summary(
            transcript_text,
            model_name=model_name,
            api_key=config.anthropic_api_key,
        )

        # Save summary
        summary_file = os.path.join(output_directory, "meeting_summary.txt")
        save_summary(summary, summary_file)

        click.echo(f"Workflow completed successfully. Summary saved to: {summary_file}")
    except Exception as e:
        logger.exception("An error occurred: {}", e)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
