from __future__ import annotations

import json
from collections.abc import Mapping

from minutia.paths import CleanupPolicy, RunPaths
from minutia.pipeline.orchestrator import (
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


def test_orchestrator_skips_disabled_steps(sample_run_paths) -> None:
    config = _make_config(sample_run_paths, skip_summary=True)

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


def test_cleanup_policy_keep_final_on_success(sample_run_paths) -> None:
    """Test that KEEP_FINAL cleanup policy removes intermediate files on success."""
    config = _make_config(sample_run_paths, cleanup_policy=CleanupPolicy.KEEP_FINAL)
    
    # Create some fake intermediate files
    config.run_paths.ensure_directories()
    config.run_paths.microphone_audio.write_text("fake audio data")
    config.run_paths.desktop_audio.write_text("fake audio data")
    config.run_paths.merged_transcript.write_text('{"fake": "transcript"}')

    def success_step(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        return {"success": "done"}

    orchestrator = PipelineOrchestrator(
        steps=[PipelineStepDefinition(name="success", runner=success_step)]
    )

    result = orchestrator.execute(config)

    assert result.success is True
    # Audio files should be removed by KEEP_FINAL policy
    assert not config.run_paths.microphone_audio.exists()
    assert not config.run_paths.desktop_audio.exists()
    # Final outputs should remain
    assert config.run_paths.merged_transcript.exists()


def test_cleanup_policy_cleanup_on_error_on_failure(sample_run_paths) -> None:
    """Test that CLEANUP_ON_ERROR policy removes entire run directory on failure."""
    config = _make_config(sample_run_paths, cleanup_policy=CleanupPolicy.CLEANUP_ON_ERROR)
    
    # Create some files
    config.run_paths.ensure_directories()
    config.run_paths.microphone_audio.write_text("fake audio data")
    config.run_paths.merged_transcript.write_text('{"fake": "transcript"}')

    def failing_step(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        raise RuntimeError("Test failure")

    orchestrator = PipelineOrchestrator(
        steps=[PipelineStepDefinition(name="failure", runner=failing_step)]
    )

    result = orchestrator.execute(config)

    assert result.success is False
    # Entire run directory should be removed
    assert not config.run_paths.run_root.exists()


def test_cleanup_policy_keep_all_preserves_files(sample_run_paths) -> None:
    """Test that KEEP_ALL policy preserves all files regardless of outcome."""
    config = _make_config(sample_run_paths, cleanup_policy=CleanupPolicy.KEEP_ALL)
    
    # Create some files
    config.run_paths.ensure_directories()
    config.run_paths.microphone_audio.write_text("fake audio data")
    config.run_paths.desktop_audio.write_text("fake audio data")
    config.run_paths.merged_transcript.write_text('{"fake": "transcript"}')

    def success_step(_: PipelineConfig, __: Mapping[str, str]) -> dict[str, str]:
        return {"success": "done"}

    orchestrator = PipelineOrchestrator(
        steps=[PipelineStepDefinition(name="success", runner=success_step)]
    )

    result = orchestrator.execute(config)

    assert result.success is True
    # All files should be preserved with KEEP_ALL policy
    assert config.run_paths.microphone_audio.exists()
    assert config.run_paths.desktop_audio.exists()
    assert config.run_paths.merged_transcript.exists()


def test_cleanup_policy_safety_checks(tmp_path) -> None:
    """Test that cleanup safety checks prevent dangerous operations."""
    from minutia.paths import CleanupPolicy, RunPaths
    
    # Test 1: Refuse to clean non-minutia directory
    dangerous_path = tmp_path / "not-a-minutia-run"
    dangerous_path.mkdir()
    
    # Create a RunPaths with a non-standard directory name
    fake_run_paths = RunPaths(
        run_root=dangerous_path,
        input_path=tmp_path / "fake.mkv",
        audio_dir=dangerous_path / "audio",
        transcripts_dir=dangerous_path / "transcripts",
        microphone_audio=dangerous_path / "audio" / "mic.wav",
        desktop_audio=dangerous_path / "audio" / "desktop.wav",
        merged_transcript=dangerous_path / "merged.json",
        summary_file=dangerous_path / "summary.txt",
        metadata_file=dangerous_path / "metadata.json",
        logs_file=dangerous_path / "minutia.log",
    )
    
    # This should raise RuntimeError due to safety checks
    try:
        fake_run_paths.cleanup(CleanupPolicy.CLEANUP_ON_ERROR)
        raise AssertionError("Expected RuntimeError for unsafe directory")
    except RuntimeError as e:
        assert "doesn't appear to be a minutia run" in str(e)
    
    # Test 2: Verify proper minutia directory gets cleaned
    proper_minutia_dir = tmp_path / "runs" / "2024-01-15_test-meeting"
    proper_minutia_dir.mkdir(parents=True)
    
    proper_run_paths = RunPaths(
        run_root=proper_minutia_dir,
        input_path=tmp_path / "meeting.mkv",
        audio_dir=proper_minutia_dir / "audio",
        transcripts_dir=proper_minutia_dir / "transcripts",
        microphone_audio=proper_minutia_dir / "audio" / "mic.wav",
        desktop_audio=proper_minutia_dir / "audio" / "desktop.wav",
        merged_transcript=proper_minutia_dir / "merged.json",
        summary_file=proper_minutia_dir / "summary.txt",
        metadata_file=proper_minutia_dir / "metadata.json",
        logs_file=proper_minutia_dir / "minutia.log",
    )
    
    # Create some test files
    proper_run_paths.ensure_directories()
    proper_run_paths.microphone_audio.write_text("test")
    proper_run_paths.merged_transcript.write_text('{"test": "data"}')
    
    # This should work safely
    proper_run_paths.cleanup(CleanupPolicy.CLEANUP_ON_ERROR)
    
    # Directory should be cleaned up
    assert not proper_minutia_dir.exists()
