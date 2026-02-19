"""Minutia: Meeting recording, transcription, and summarization tool."""

__version__ = "0.1.0"

from .cli import main
from . import steps, pipeline, clients, config, logging, paths, run_metadata
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
