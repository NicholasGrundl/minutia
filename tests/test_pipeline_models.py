from pathlib import Path

from minutia.pipeline import PipelineConfig, PipelineResult, StepProgress, StepStatus


def test_pipeline_config_defaults(sample_run_paths):
    run_paths = sample_run_paths
    config = PipelineConfig(
        input_path=run_paths.input_path,
        run_paths=run_paths,
        run_id="20250101T000000Z",
    )

    assert config.whisper_model == "base"
    assert config.summary_model == "claude-4-5-sonnet"
    assert config.mic_track == 3
    assert config.desktop_track == 2
    assert config.base_output_dir == Path("./runs")
    assert config.anthropic_api_key is None
    assert config.log_level == "INFO"


def test_step_progress_representation():
    progress = StepProgress(step_name="extract_audio", status=StepStatus.RUNNING, message="starting")
    assert progress.step_name == "extract_audio"
    assert progress.status is StepStatus.RUNNING
    assert progress.message == "starting"
    assert progress.error is None


def test_pipeline_result_defaults(tmp_path):
    run_paths = create_run_paths(tmp_path)
    result = PipelineResult(success=True, run_paths=run_paths)

    assert result.success is True
    assert result.completed_steps == []
    assert result.failed_step is None
    assert result.error is None
    assert result.artifacts == {}
    assert result.duration_seconds is None


def test_pipeline_result_failure_data(tmp_path):
    run_paths = create_run_paths(tmp_path)
    error = RuntimeError("boom")
    result = PipelineResult(
        success=False,
        run_paths=run_paths,
        completed_steps=["extract_audio"],
        failed_step="transcribe",
        error=error,
        artifacts={"extract_audio": {"microphone": "mic.wav"}},
        duration_seconds=12.5,
    )

    assert result.success is False
    assert result.failed_step == "transcribe"
    assert result.error is error
    assert result.completed_steps == ["extract_audio"]
    assert result.artifacts["extract_audio"]["microphone"] == "mic.wav"
    assert result.duration_seconds == 12.5


def test_pipeline_config_custom_summary_model(tmp_path):
    run_paths = create_run_paths(tmp_path)
    config = PipelineConfig(
        input_path=run_paths.input_path,
        run_paths=run_paths,
        run_id="20250101T000000Z",
        summary_model="claude-3-haiku",
    )

    assert config.summary_model == "claude-3-haiku"


def test_pipeline_config_log_level_normalisation(tmp_path):
    run_paths = create_run_paths(tmp_path)
    config = PipelineConfig(
        input_path=run_paths.input_path,
        run_paths=run_paths,
        run_id="run",
        log_level="debug",
    )

    assert config.log_level == "DEBUG"
