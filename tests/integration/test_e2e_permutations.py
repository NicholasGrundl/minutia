"""Integration coverage for pipeline failures and partial completion."""

from pathlib import Path

import pytest

from minutia.paths import RunPaths
from minutia.pipeline.orchestrator import PipelineConfig, PipelineOrchestrator


def _default_steps_through(step_name: str):
    """Return the real orchestrator adapters through the named step."""
    steps = PipelineOrchestrator().steps
    end = next(index for index, step in enumerate(steps) if step.name == step_name)
    return steps[: end + 1]


class TestE2EPermutations:
    """Exercise failure modes using the production orchestration contract."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_ffmpeg, mock_whisper, mock_llm, chaos_config):
        self.mock_ffmpeg = mock_ffmpeg
        self.mock_whisper = mock_whisper
        self.mock_llm = mock_llm
        self.chaos_config = chaos_config

    def test_missing_video_file_fails_gracefully(self, tmp_path):
        missing_video = tmp_path / "non_existent.mkv"
        missing_video.touch()
        run_paths = RunPaths.from_video_input(
            missing_video, base_output_dir=tmp_path / "runs"
        )
        missing_video.unlink()
        config = PipelineConfig(
            input_path=missing_video,
            run_paths=run_paths,
            run_id="missing-video-test",
        )

        with self.chaos_config.set_error(
            "ffmpeg.probe", FileNotFoundError(f"Video not found: {missing_video}")
        ):
            result = PipelineOrchestrator(
                steps=_default_steps_through("extract_audio")
            ).execute(config)

        assert result.success is False
        assert result.failed_step == "extract_audio"
        assert "not found" in str(result.error).lower()

    def test_missing_audio_track_fails_extraction(self, scenario_loader, tmp_path):
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=0)
        run_paths = RunPaths.from_video_input(
            input_video, base_output_dir=tmp_path / "runs"
        )
        config = PipelineConfig(
            input_path=input_video,
            run_paths=run_paths,
            run_id="missing-track-test",
            mic_track=1,
        )

        result = PipelineOrchestrator(
            steps=_default_steps_through("extract_audio")
        ).execute(config)

        assert result.success is False
        assert result.failed_step == "extract_audio"
        assert "could not identify" in str(result.error).lower()

    def test_partial_completion_uses_existing_audio(self, scenario_loader, tmp_path):
        """A run can begin at transcription when extraction artifacts exist."""
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        run_paths = RunPaths.from_video_input(
            input_video, base_output_dir=tmp_path / "runs"
        )
        run_paths.ensure_directories()
        run_paths.microphone_audio.write_text("fake mic audio", encoding="utf-8")
        run_paths.desktop_audio.write_text("fake desktop audio", encoding="utf-8")
        self.mock_whisper.set_scenario(
            "microphone_audio",
            [{"start": 0.0, "end": 1.0, "text": "Recovered text"}],
        )
        config = PipelineConfig(
            input_path=input_video,
            run_paths=run_paths,
            run_id="partial-completion-test",
        )
        transcribe_step = _default_steps_through("transcribe")[-1]

        result = PipelineOrchestrator(steps=[transcribe_step]).execute(config)

        assert result.success is True
        assert result.completed_steps == ["transcribe"]
        assert Path(result.artifacts["microphone_transcript"]).is_file()
        assert Path(result.artifacts["desktop_transcript"]).is_file()

    @pytest.mark.parametrize(
        ("failed_step_name", "error_message"),
        [
            ("transcribe", "Whisper error"),
            ("summarize", "Anthropic API error"),
        ],
    )
    def test_pipeline_failure_preserves_partial_artifacts(
        self,
        scenario_loader,
        tmp_path,
        failed_step_name,
        error_message,
    ):
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        run_paths = RunPaths.from_video_input(
            input_video, base_output_dir=tmp_path / "runs"
        )
        self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=3)
        self.mock_whisper.set_scenario(
            "microphone_audio",
            [{"start": 0.0, "end": 1.0, "text": "some mic text"}],
        )
        self.mock_whisper.set_scenario(
            "desktop_audio",
            [{"start": 1.0, "end": 2.0, "text": "some desktop text"}],
        )
        config = PipelineConfig(
            input_path=input_video,
            run_paths=run_paths,
            run_id=f"fail-{failed_step_name}",
            anthropic_api_key="fake-api-key",
        )
        failure_point = (
            "whisper.transcribe"
            if failed_step_name == "transcribe"
            else "anthropic.messages.create"
        )

        with self.chaos_config.set_error(failure_point, RuntimeError(error_message)):
            result = PipelineOrchestrator(
                steps=_default_steps_through(failed_step_name)
            ).execute(config)

        assert result.success is False
        assert result.failed_step == failed_step_name
        assert error_message in str(result.error)
        assert run_paths.microphone_audio.exists()
        if failed_step_name == "summarize":
            assert run_paths.merged_transcript.exists()
