"""Minutia: Meeting recording, transcription, and summarization tool."""

from importlib import import_module
from typing import TYPE_CHECKING

__version__ = "0.1.0"

from . import clients, config, logging, paths, pipeline, run_metadata, steps
from .cli import main

# Cold-start discipline: the heavy step modules (torch/whisper via `audio_transcription`,
# anthropic via `summarize_transcript`, ffmpeg via `video_extraction`) are exposed **lazily**
# so that `import minutia` — and therefore the CLI's `--help` / `--version` / `config` — never
# pull the ML/AI stack. They load on first attribute access or `from minutia import <name>`
# (PEP 562). Import them directly (`minutia.steps.audio_transcription`) when you want them eagerly.
_LAZY_STEP_MODULES = frozenset(
    {
        "audio_transcription",
        "summarize_transcript",
        "transcript_merger",
        "video_extraction",
    }
)


def __getattr__(name: str):
    if name in _LAZY_STEP_MODULES:
        module = import_module(f".steps.{name}", __name__)
        globals()[name] = module  # cache so subsequent access skips __getattr__
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # keep static tooling / autocomplete aware of the lazy names
    from .steps import (
        audio_transcription,
        summarize_transcript,
        transcript_merger,
        video_extraction,
    )

__all__ = [
    "main",
    "steps",
    "pipeline",
    "clients",
    "config",
    "logging",
    "paths",
    "run_metadata",
    "audio_transcription",
    "summarize_transcript",
    "transcript_merger",
    "video_extraction",
]
