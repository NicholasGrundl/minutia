"""The ``minutia run`` command group.

``minutia run pipeline`` executes the whole pipeline non-interactively (extract → transcribe →
merge → summarize) on the shared step helpers in :mod:`._steps` — never the orchestrator. The other
subcommands run a single stage each. Bare ``minutia run`` lists them (help). This group supersedes
the old top-level step commands plus ``process-all`` (removed).

``run pipeline`` is a leaf command, so it takes a positional ``INPUT`` (the recording) like the old
``process-all`` did — the full pipeline lives under its own name rather than the bare group callback,
which keeps ``run <step>`` unambiguous and lets the positional argument work.
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import click
import typer

from ..logging import logger
from ..model_registry import anthropic_models
from ..prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds
from ._steps import (
    _extract_audio_step,
    _resolve_input_or_fail,
    _summarize_step,
    _transcribe_step,
    run_full_pipeline,
)

# Enums drive typer's CLI choices (click.Choice equivalent); both derive from their single source
# of truth so the CLI can never drift from validation.
SummaryModel = Enum(
    "SummaryModel", {choice: choice for choice in anthropic_models}, type=str
)
PromptKind = Enum("PromptKind", {kind: kind for kind in list_prompt_kinds()}, type=str)

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
PromptKindOption = Annotated[
    PromptKind,
    typer.Option("--prompt-kind", help="Which summary prompt flavor to use"),
]
NotesOption = Annotated[
    Path | None,
    typer.Option("--notes", help="Per-meeting notes/speaker-mapping markdown file"),
]
PersonalInfoOption = Annotated[
    Path | None,
    typer.Option(
        "--personal-info",
        help="Personal-info file for the prompt (defaults to configuration)",
    ),
]
GpuOption = Annotated[
    bool, typer.Option("--gpu/--no-gpu", help="Use GPU acceleration if available")
]
DryRunOption = Annotated[
    bool,
    typer.Option("--dry-run", help="Estimate tokens and price without generating summary"),
]
YesOption = Annotated[
    bool, typer.Option("--yes", "-y", help="Skip the cost confirmation prompt")
]

run_app = typer.Typer(
    name="run",
    help="Run the pipeline — `run pipeline` does the whole thing; the others run one stage.",
    add_completion=False,
    no_args_is_help=True,
)


@run_app.command("pipeline")
def pipeline(
    ctx: typer.Context,
    input_video: Annotated[Path | None, typer.Argument(exists=True)] = None,
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    mic_track: MicTrackOption = None,
    desktop_track: DesktopTrackOption = None,
    model: SummaryModelOption = None,
    prompt_kind: PromptKindOption = PromptKind(DEFAULT_PROMPT_KIND),
    notes: NotesOption = None,
    personal_info: PersonalInfoOption = None,
    gpu: GpuOption = True,
    force: ForceOption = False,
    dry_run: DryRunOption = False,
    yes: YesOption = False,
):
    """Run the whole pipeline non-interactively (newest recording when no input given)."""
    config = ctx.obj["config"]
    input_path = _resolve_input_or_fail(config, input_video)
    model_name = model.value if model else config.summary_model
    output_directory = (
        output_dir.expanduser()
        if output_dir
        else config.base_output_dir / input_path.stem
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Working in: {output_directory}")
    try:
        run_full_pipeline(
            config,
            input_path,
            output_directory,
            prompt_kind=prompt_kind.value,
            notes_path=notes.expanduser() if notes else None,
            model_name=model_name,
            mic_track=mic_track,
            desktop_track=desktop_track,
            personal_info_path=personal_info,
            gpu=gpu,
            force=force,
            dry_run=dry_run,
            yes=yes,
        )
    except (click.ClickException, click.exceptions.Abort):
        raise
    except Exception as e:
        logger.exception("Pipeline run failed: {}", e)
        raise click.ClickException(str(e)) from e


@run_app.command("extract-audio")
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


@run_app.command()
def transcribe(
    ctx: typer.Context,
    mic_audio: Annotated[Path, typer.Argument(exists=True)],
    desktop_audio: Annotated[Path, typer.Argument(exists=True)],
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    whisper_model: Annotated[
        str | None,
        typer.Option(help="Whisper model name (defaults to configuration)"),
    ] = None,
    gpu: GpuOption = True,
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


@run_app.command()
def merge(
    ctx: typer.Context,
    mic_transcript: Annotated[Path, typer.Argument(exists=True)],
    desktop_transcript: Annotated[Path, typer.Argument(exists=True)],
    output_file: Annotated[Path, typer.Argument()],
):
    """Merge microphone and desktop transcripts."""
    from ..steps.transcript_merger import process_transcripts

    try:
        process_transcripts(
            str(mic_transcript), str(desktop_transcript), str(output_file)
        )
        typer.echo(f"Merged transcript saved to: {output_file}")
    except Exception as e:
        logger.exception("Transcript merging failed: {}", e)
        raise click.ClickException(str(e)) from e


@run_app.command()
def summarize(
    ctx: typer.Context,
    merged_transcript: Annotated[Path, typer.Argument(exists=True)],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            help="Where the markdown report is written (default: next to the transcript)"
        ),
    ] = None,
    prompt_kind: PromptKindOption = PromptKind(DEFAULT_PROMPT_KIND),
    notes: NotesOption = None,
    personal_info: PersonalInfoOption = None,
    model: SummaryModelOption = None,
    dry_run: DryRunOption = False,
    yes: YesOption = False,
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
