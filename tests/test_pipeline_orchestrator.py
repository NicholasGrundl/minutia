from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from minutia.paths import RunPaths
from minutia.pipeline import (
    PipelineConfig,
    PipelineOrchestrator,
    PipelineStepDefinition,
    StepProgress,
    StepStatus,
)


def _make_config(sample_run_paths: RunPaths, **overrides) -> PipelineConfig:
    return PipelineConfig(
        input_path=sample_run_paths.input_path,
        run_paths=sample_run_paths,
        run_id="test-run",
        **overrides,
    )


def test_orchestrator_executes_steps_and_collects_artifacts(sample_run_paths) -> None:
    config = _make_config(sample_run_paths)
    progress_events: list[StepProgress] = []

    def first_step(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        return {"first": "done"}

    def second_step(_: PipelineConfig, artifacts: Mapping[str, str]) -> dict[str, str]:
        assert artifacts["first"] == "done"
        return {"second": "done"}

    orchestrator = PipelineOrchestrator(
        steps=[
            PipelineStepDefinition(name="first", runner=first_step, description="First step"),
            PipelineStepDefinition(name="second", runner=second_step, description="Second step"),
        ],
        progress_callback=progress_events.append,
    )

    result = orchestrator.execute(config)

    assert result.success is True
    assert result.completed_steps == ["first", "second"]
    assert result.artifacts["first"] == "done"
    assert result.artifacts["second"] == "done"

    assert orchestrator.state.success is True
    assert orchestrator.state.completed_steps == ["first", "second"]
    assert orchestrator.state.error is None

    statuses = [(event.step_name, event.status) for event in progress_events]
    assert statuses == [
        ("first", StepStatus.RUNNING),
        ("first", StepStatus.COMPLETED),
        ("second", StepStatus.RUNNING),
        ("second", StepStatus.COMPLETED),
    ]

    metadata_path = config.run_paths.metadata_file
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["run_info"]["status"] == "completed"


def test_orchestrator_handles_step_failure(sample_run_paths) -> None:
    config = _make_config(sample_run_paths)
    progress_events: list[StepProgress] = []

    def succeeds(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        return {"ok": "done"}

    def fails(_: PipelineConfig, artifacts: Mapping[str, str]) -> dict[str, str]:
        assert artifacts["ok"] == "done"
        raise RuntimeError("boom")

    orchestrator = PipelineOrchestrator(
        steps=[
            PipelineStepDefinition(name="success", runner=succeeds),
            PipelineStepDefinition(name="failure", runner=fails),
        ],
        progress_callback=progress_events.append,
    )

    result = orchestrator.execute(config)

    assert result.success is False
    assert result.failed_step == "failure"
    assert isinstance(result.error, RuntimeError)
    assert result.completed_steps == ["success"]
    assert result.artifacts["ok"] == "done"

    assert orchestrator.state.success is False
    assert orchestrator.state.failed_step == "failure"
    assert isinstance(orchestrator.state.error, RuntimeError)

    assert progress_events[-1].status is StepStatus.FAILED
    assert progress_events[-1].step_name == "failure"

    metadata_path = config.run_paths.metadata_file
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["run_info"]["status"] == "failed"


def test_orchestrator_skips_disabled_steps(tmp_path: Path) -> None:
    config = _make_config(tmp_path, skip_summary=True)

    progress_events: list[StepProgress] = []

    def runner(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        return {"ran": "yes"}

    orchestrator = PipelineOrchestrator(
        steps=[
            PipelineStepDefinition(name="always", runner=runner),
            PipelineStepDefinition(name="maybe", runner=runner, is_enabled=lambda cfg: not cfg.skip_summary),
        ],
        progress_callback=progress_events.append,
    )

    result = orchestrator.execute(config)

    assert result.success is True
    assert result.completed_steps == ["always"]
    assert "ran" in result.artifacts

    emitted = [(event.step_name, event.status, event.message) for event in progress_events]
    assert emitted[0] == ("always", StepStatus.RUNNING, "")
    assert emitted[1] == ("always", StepStatus.COMPLETED, "Completed")
    assert emitted[2] == ("maybe", StepStatus.COMPLETED, "Skipped")

    metadata_path = config.run_paths.metadata_file
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["run_info"]["status"] == "completed"
