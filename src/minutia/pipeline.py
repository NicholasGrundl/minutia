"""
Data structures and enums for the Minutia pipeline.

This module defines the core data structures used for configuring, executing,
and reporting results from a Minutia processing pipeline. These types provide
the foundation for the pipeline orchestrator, ensuring consistent state
management and clear communication between pipeline steps.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .paths import RunPaths


class StepStatus(Enum):
    """
    Represents the lifecycle status of an individual pipeline step.

    Attributes
    ----------
    PENDING
        The step has not yet started.
    RUNNING
        The step is currently in progress.
    COMPLETED
        The step finished successfully.
    FAILED
        The step terminated with an error.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class StepProgress:
    """
    A snapshot of a pipeline step's progress.

    These events are emitted by pipeline steps to report their status back to
    the orchestrator and any listening UIs.

    Attributes
    ----------
    step_name : str
        The name of the pipeline step (e.g., 'extract_audio').
    status : StepStatus
        The current execution status of the step.
    message : str, optional
        A human-readable message describing the current activity.
    error : Exception, optional
        The exception object if the step has failed.
    """

    step_name: str
    status: StepStatus
    message: str = ""
    error: Optional[Exception] = None


class PipelineStep(Enum):
    """
    Identifiers for the default Minutia pipeline steps.

    The orchestrator executes steps in this order by default. Additional steps
    can be supplied through the orchestrator constructor for extensibility and
    testing.
    """

    EXTRACT_AUDIO = "extract_audio"
    TRANSCRIBE = "transcribe"
    MERGE = "merge"
    SUMMARIZE = "summarize"


def _always_enabled(_: PipelineConfig) -> bool:
    """Predicate used when a step is always executed."""
    return True


@dataclass
class PipelineStepDefinition:
    """
    Describes a single executable pipeline step.

    Attributes
    ----------
    name
        Unique identifier for the step. Defaults use :class:`PipelineStep` values
        but arbitrary strings are accepted for custom pipelines.
    runner
        Callable that performs the work for the step. It receives the pipeline
        configuration and a read-only mapping of previously produced artifacts,
        returning a dictionary of new artifacts for downstream steps.
    description
        Optional human-friendly text included in progress updates.
    is_enabled
        Predicate that determines whether the step should run for a given
        configuration (e.g., skip summary when ``skip_summary`` is true).
    """

    name: str
    runner: StepRunner
    description: str = ""
    is_enabled: Callable[[PipelineConfig], bool] = _always_enabled

    def __post_init__(self) -> None:
        if not callable(self.runner):
            raise TypeError("runner must be callable")
        if not callable(self.is_enabled):
            raise TypeError("is_enabled must be callable")


@dataclass(frozen=True)
class PipelineConfig:
    """
    Configuration for a single pipeline execution.

    This structure holds all the necessary parameters to initialize and run
    the full transcription and summarization pipeline.

    Attributes
    ----------
    input_path : Path
        The absolute path to the primary input file (e.g., video or audio).
    run_paths : RunPaths
        The canonical set of filesystem paths for the run.
    run_id : str
        A unique identifier for this specific pipeline run.
    whisper_model : str, default='base'
        The name of the Whisper model to use for transcription (e.g., 'tiny',
        'base', 'small', 'medium', 'large').
    skip_summary : bool, default=False
        If True, the final summarization step will be skipped.
    summary_model : str, default='claude-4-5-sonnet'
        The Anthropic model identifier to use for summarization.
    mic_track : int, default=3
        The audio track number for the microphone in the source video.
    desktop_track : int, default=2
        The audio track number for the desktop audio in the source video.
    base_output_dir : Path, default=Path('./runs')
        The parent directory where all run-specific output folders are created.
    """

    input_path: Path
    run_paths: RunPaths
    run_id: str
    whisper_model: str = "base"
    skip_summary: bool = False
    summary_model: str = "claude-4-5-sonnet"
    mic_track: int = 3
    desktop_track: int = 2
    base_output_dir: Path = Path("./runs")


StepRunner = Callable[[PipelineConfig, Mapping[str, Any]], Dict[str, Any]]
ProgressCallback = Callable[[StepProgress], None]


@dataclass
class PipelineResult:
    """
    The final result of a completed pipeline execution.

    This object aggregates all outputs and metadata from a pipeline run,
    indicating whether it succeeded or failed and providing access to the
    generated artifacts.

    Attributes
    ----------
    success : bool
        True if all pipeline steps completed successfully, False otherwise.
    run_paths : RunPaths
        The filesystem paths used during the run.
    completed_steps : List[str]
        A list of names of the steps that completed successfully.
    failed_step : str, optional
        The name of the step that failed, if any.
    error : Exception, optional
        The exception that caused the pipeline to fail.
    artifacts : Dict[str, Any]
        A dictionary of key artifacts produced during the run, such as the
        final transcript content or summary.
    duration_seconds : float, optional
        The total time taken for the pipeline execution in seconds.
    """

    success: bool
    run_paths: RunPaths
    completed_steps: List[str] = field(default_factory=list)
    failed_step: Optional[str] = None
    error: Optional[Exception] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: Optional[float] = None

    @property
    def is_partial(self) -> bool:
        """True when at least one step finished but the pipeline failed overall."""
        return bool(self.completed_steps) and not self.success


@dataclass
class PipelineExecutionState:
    """
    Mutable orchestration state captured during pipeline execution.

    The orchestrator stores the current step, artifacts produced so far, and
    any failure information so callers can inspect progress in real time.
    """

    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    failed_step: Optional[str] = None
    error: Optional[Exception] = None
    success: Optional[bool] = None


class PipelineOrchestrator:
    """
    Coordinate the Minutia pipeline steps with progress callbacks.

    The orchestrator executes configured steps sequentially, emitting
    :class:`StepProgress` events and producing a :class:`PipelineResult`.
    """

    def __init__(
        self,
        steps: Optional[Sequence[PipelineStepDefinition]] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        self._custom_steps = list(steps) if steps is not None else None
        self._progress_callback = progress_callback or (lambda progress: None)
        self.state = PipelineExecutionState()

    def _build_default_steps(self) -> List[PipelineStepDefinition]:
        """
        Construct the default pipeline step sequence.

        The concrete implementations are imported lazily to avoid heavy
        dependencies during module import (e.g., Whisper, ffmpeg).
        """

        def extract_audio(config: PipelineConfig, _: Mapping[str, Any]) -> Dict[str, Any]:
            from . import video_extraction

            config.run_paths.ensure_directories()
            outputs = video_extraction.process_mkv_file(
                str(config.input_path),
                str(config.run_paths.audio_dir),
                mic_track_number=config.mic_track,
                desktop_track_number=config.desktop_track,
            )
            return {
                "microphone_audio": config.run_paths.microphone_audio,
                "desktop_audio": config.run_paths.desktop_audio,
                "extract_audio": {key: Path(value) for key, value in outputs.items()},
            }

        def transcribe(config: PipelineConfig, artifacts: Mapping[str, Any]) -> Dict[str, Any]:
            from . import audio_transcription

            mic_audio = artifacts.get("microphone_audio") or config.run_paths.microphone_audio
            desk_audio = artifacts.get("desktop_audio") or config.run_paths.desktop_audio
            outputs = audio_transcription.process_audio_files(
                str(mic_audio),
                str(desk_audio),
                str(config.run_paths.transcripts_dir),
                whisper_model_name=config.whisper_model,
            )
            return {
                "microphone_transcript": Path(outputs["microphone"]),
                "desktop_transcript": Path(outputs["desktop"]),
                "transcribe": {key: Path(value) for key, value in outputs.items()},
            }

        def merge(config: PipelineConfig, artifacts: Mapping[str, Any]) -> Dict[str, Any]:
            from . import transcript_merger

            microphone = artifacts.get("microphone_transcript")
            desktop = artifacts.get("desktop_transcript")
            if microphone is None or desktop is None:
                raise RuntimeError("Transcription artifacts missing for merge step.")
            transcript_merger.process_transcripts(
                str(microphone),
                str(desktop),
                str(config.run_paths.merged_transcript),
            )
            return {"merged_transcript": config.run_paths.merged_transcript}

        def summarize(config: PipelineConfig, artifacts: Mapping[str, Any]) -> Dict[str, Any]:
            from . import summarize_transcript

            merged_path = artifacts.get("merged_transcript") or config.run_paths.merged_transcript
            transcript_data = summarize_transcript.load_transcript(str(merged_path))
            transcript_text = summarize_transcript.prepare_transcript_for_summary(transcript_data)
            summary_text = summarize_transcript.generate_summary(
                transcript_text,
                model_name=config.summary_model,
            )
            summarize_transcript.save_summary(summary_text, str(config.run_paths.summary_file))
            return {
                "summary": config.run_paths.summary_file,
                "summary_text": summary_text,
            }

        return [
            PipelineStepDefinition(
                name=PipelineStep.EXTRACT_AUDIO.value,
                runner=extract_audio,
                description="Extracting audio tracks",
            ),
            PipelineStepDefinition(
                name=PipelineStep.TRANSCRIBE.value,
                runner=transcribe,
                description="Transcribing audio with Whisper",
            ),
            PipelineStepDefinition(
                name=PipelineStep.MERGE.value,
                runner=merge,
                description="Merging transcripts",
            ),
            PipelineStepDefinition(
                name=PipelineStep.SUMMARIZE.value,
                runner=summarize,
                description="Generating meeting summary",
                is_enabled=lambda cfg: not cfg.skip_summary,
            ),
        ]

    @property
    def steps(self) -> List[PipelineStepDefinition]:
        """Return the active step sequence."""
        return list(self._custom_steps if self._custom_steps is not None else self._build_default_steps())

    def _report_progress(self, step_name: str, status: StepStatus, message: str = "", error: Optional[Exception] = None) -> None:
        """Emit a progress update to the registered callback."""
        progress = StepProgress(step_name=step_name, status=status, message=message, error=error)
        self._progress_callback(progress)

    def execute(self, config: PipelineConfig) -> PipelineResult:
        """
        Execute the pipeline steps sequentially and return the outcome.

        Exceptions raised by individual steps are caught so the caller receives
        a :class:`PipelineResult` containing partial progress information.
        """
        config.run_paths.ensure_directories()

        artifacts: Dict[str, Any] = {}
        completed_steps: List[str] = []
        start_time = time.perf_counter()
        self.state = PipelineExecutionState()
        self.state.success = None

        for step in self.steps:
            if not step.is_enabled(config):
                self._report_progress(step.name, StepStatus.COMPLETED, "Skipped")
                continue

            self.state.current_step = step.name
            self._report_progress(step.name, StepStatus.RUNNING, step.description)

            try:
                step_outputs = step.runner(config, MappingProxyType(artifacts))
                if step_outputs:
                    artifacts.update(step_outputs)
                completed_steps.append(step.name)
                self.state.completed_steps = list(completed_steps)
                self.state.artifacts = dict(artifacts)
                self._report_progress(step.name, StepStatus.COMPLETED, "Completed")
            except Exception as exc:  # noqa: BLE001 - propagate structured failure state
                self.state.failed_step = step.name
                self.state.error = exc
                self.state.success = False
                self._report_progress(step.name, StepStatus.FAILED, str(exc), error=exc)
                return PipelineResult(
                    success=False,
                    run_paths=config.run_paths,
                    completed_steps=list(completed_steps),
                    failed_step=step.name,
                    error=exc,
                    artifacts=dict(artifacts),
                    duration_seconds=time.perf_counter() - start_time,
                )

        self.state.current_step = None
        self.state.success = True

        return PipelineResult(
            success=True,
            run_paths=config.run_paths,
            completed_steps=list(completed_steps),
            artifacts=dict(artifacts),
            duration_seconds=time.perf_counter() - start_time,
        )
