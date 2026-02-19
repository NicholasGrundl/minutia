from __future__ import annotations

from click.testing import CliRunner

import minutia.cli
from minutia.pipeline.orchestrator import PipelineResult, StepProgress, StepStatus


def test_process_all_runs_pipeline_orchestrator(sample_video_file, tmp_path, monkeypatch):
    """Ensure the CLI wraps the pipeline orchestrator and reports artifacts."""
    input_video = sample_video_file

    env = {
        "MINUTIA_OUTPUT_DIR": str(tmp_path / "runs"),
        "MINUTIA_WHISPER_MODEL": "base",
    }

    captured_config: dict[str, object] = {}

    class StubOrchestrator:
        def __init__(self, progress_callback=None):
            self.progress_callback = progress_callback

        def execute(self, config):
            captured_config["config"] = config
            run_paths = config.run_paths
            run_paths.ensure_directories()

            # Create artifacts expected by the CLI output summary.
            run_paths.microphone_audio.write_text("mic", encoding="utf-8")
            run_paths.desktop_audio.write_text("desktop", encoding="utf-8")
            run_paths.merged_transcript.write_text("{}", encoding="utf-8")
            run_paths.summary_file.write_text("summary", encoding="utf-8")

            if self.progress_callback:
                self.progress_callback(
                    StepProgress(
                        step_name="extract_audio",
                        status=StepStatus.RUNNING,
                        message="Extracting audio tracks",
                    )
                )
                self.progress_callback(
                    StepProgress(
                        step_name="extract_audio",
                        status=StepStatus.COMPLETED,
                        message="Completed",
                    )
                )

            return PipelineResult(
                success=True,
                run_paths=run_paths,
                completed_steps=[
                    "extract_audio",
                    "transcribe",
                    "merge",
                    "summarize",
                ],
                artifacts={"summary": run_paths.summary_file},
            )

    monkeypatch.setattr(minutia.cli, "PipelineOrchestrator", StubOrchestrator)

    runner = CliRunner()
    result = runner.invoke(minutia.cli.main, ["process-all", str(input_video)], env=env)

    assert result.exit_code == 0, result.output
    config = captured_config["config"]
    assert config.summary_model == "claude-4-5-sonnet"
    assert config.run_paths.run_root.exists()

    output = result.output
    assert "[RUNNING] extract_audio" in output
    assert "[COMPLETED] extract_audio" in output
    assert "Pipeline completed successfully." in output
    assert str(config.run_paths.run_root) in output
    assert str(config.run_paths.summary_file) in output
