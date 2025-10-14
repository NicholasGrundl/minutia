"""
Data structures and enums supporting the Minutia pipeline orchestration.

The orchestrator implementation will build on top of these foundational types to
manage step execution, progress reporting, and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import RunPaths


class StepStatus(Enum):
    """Lifecycle states for individual pipeline steps."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class StepProgress:
    """Progress event emitted by pipeline steps."""

    step_name: str
    status: StepStatus
    message: str = ""
    error: Optional[Exception] = None


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration required to execute a pipeline run."""

    input_path: Path
    run_paths: RunPaths
    run_id: str
    whisper_model: str = "base"
    skip_summary: bool = False
    mic_track: int = 3
    desktop_track: int = 2
    base_output_dir: Path = Path("./runs")


@dataclass
class PipelineResult:
    """Aggregate result of a pipeline execution."""

    success: bool
    run_paths: RunPaths
    completed_steps: List[str] = field(default_factory=list)
    failed_step: Optional[str] = None
    error: Optional[Exception] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: Optional[float] = None
