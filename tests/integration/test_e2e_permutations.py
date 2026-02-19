import pytest
from pathlib import Path
from minutia.pipeline.orchestrator import PipelineOrchestrator, PipelineConfig, PipelineStepDefinition
from minutia.steps import video_extraction, audio_transcription, transcript_merger, summarize_transcript

class TestE2EPermutations:
    """
    End-to-End integration tests for various pipeline permutations,
    failure modes, and partial completion states.
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_ffmpeg, mock_whisper, mock_llm, chaos_config):
        self.mock_ffmpeg = mock_ffmpeg
        self.mock_whisper = mock_whisper
        self.mock_llm = mock_llm
        self.chaos_config = chaos_config

    def _get_video_extraction_step(self):
        return PipelineStepDefinition(
            name="extract_audio",
            runner=video_extraction.process_mkv_file,
            description="Extract audio tracks from MKV"
        )

    def _get_transcription_step(self):
        return PipelineStepDefinition(
            name="transcribe",
            runner=audio_transcription.transcribe_audio_files,
            description="Transcribe audio files using Whisper"
        )

    def _get_merger_step(self):
        return PipelineStepDefinition(
            name="merge",
            runner=transcript_merger.process_transcripts,
            description="Merge transcripts into a single JSON"
        )

    def _get_summary_step(self):
        return PipelineStepDefinition(
            name="summarize",
            runner=summarize_transcript.summarize_run,
            description="Summarize merged transcript using LLM"
        )

    def test_missing_video_file_fails_gracefully(self, tmp_path, sample_run_paths):
        """Test that the pipeline fails immediately if the input video is missing."""
        # Ensure input doesn't exist
        missing_video = tmp_path / "non_existent.mkv"
        
        config = PipelineConfig(
            input_path=missing_video,
            run_paths=sample_run_paths,
            run_id="missing-video-test"
        )
        
        orchestrator = PipelineOrchestrator(
            steps=[self._get_video_extraction_step()]
        )
        
        result = orchestrator.execute(config)
        
        assert result.success is False
        assert result.failed_step == "extract_audio"
        assert "not found" in str(result.error).lower()

    def test_missing_audio_track_fails_extraction(self, scenario_loader, tmp_path):
        """Test failure when the requested audio track is missing from the video."""
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        
        # Configure FFmpeg to report NO tracks (or just not the ones we want)
        self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=0)
        
        from minutia.paths import RunPaths
        run_paths = RunPaths.from_video_input(input_video, base_output_dir=tmp_path / "runs")
        
        config = PipelineConfig(
            input_path=input_video,
            run_paths=run_paths,
            run_id="missing-track-test",
            mic_track=1 # FFmpeg probe says 0 tracks
        )
        
        orchestrator = PipelineOrchestrator(
            steps=[self._get_video_extraction_step()]
        )
        
        result = orchestrator.execute(config)
        
        assert result.success is False
        assert result.failed_step == "extract_audio"
        assert "no audio tracks found" in str(result.error).lower()

    def test_partial_completion_audio_already_exists(self, scenario_loader, tmp_path):
        """
        Test that the pipeline can proceed if some artifacts already exist.
        In this case, audio is already extracted, so we skip extraction or it just works.
        """
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        
        from minutia.paths import RunPaths
        run_paths = RunPaths.from_video_input(input_video, base_output_dir=tmp_path / "runs")
        run_paths.ensure_directories()
        
        # Pre-place the audio file
        run_paths.microphone_audio.write_text("fake audio", encoding="utf-8")
        
        # Configure mocks
        self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=1)
        self.mock_whisper.set_scenario("microphone_audio", [{"start": 0.0, "end": 1.0, "text": "Recovered text"}])
        
        config = PipelineConfig(
            input_path=input_video,
            run_paths=run_paths,
            run_id="partial-completion-test"
        )
        
        orchestrator = PipelineOrchestrator(
            steps=[
                self._get_video_extraction_step(),
                self._get_transcription_step()
            ]
        )
        
        result = orchestrator.execute(config)
        
        assert result.success is True
        assert "extract_audio" in result.completed_steps
        assert "transcribe" in result.completed_steps
        assert run_paths.transcripts_dir.exists()

    @pytest.mark.parametrize("failed_step_name, error_msg", [
        ("transcribe", "Whisper error"),
        ("summarize", "Anthropic API error"),
    ])
    def test_pipeline_failure_preserves_partial_artifacts(self, scenario_loader, tmp_path, failed_step_name, error_msg):
        """Test that a failure in a later step preserves artifacts from earlier steps."""
        scenario = scenario_loader("microphone_only")
        input_video = scenario["path"] / "input.mkv"
        
        from minutia.paths import RunPaths
        run_paths = RunPaths.from_video_input(input_video, base_output_dir=tmp_path / "runs")
        
        # Configure mocks to fail
        if failed_step_name == "transcribe":
            with self.chaos_config.set_error("whisper.transcribe", RuntimeError(error_msg)):
                self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=1)
                
                orchestrator = PipelineOrchestrator(
                    steps=[
                        self._get_video_extraction_step(),
                        self._get_transcription_step()
                    ]
                )
                result = orchestrator.execute(PipelineConfig(input_path=input_video, run_paths=run_paths, run_id="fail-transcribe"))
        else:
            self.mock_ffmpeg.set_probe_data(input_video, audio_tracks=1)
            self.mock_whisper.set_scenario("microphone_audio", [{"start": 0.0, "end": 1.0, "text": "some text"}])
            
            with self.chaos_config.set_error("llm.generate", RuntimeError(error_msg)):
                orchestrator = PipelineOrchestrator(
                    steps=[
                        self._get_video_extraction_step(),
                        self._get_transcription_step(),
                        self._get_merger_step(),
                        self._get_summary_step()
                    ]
                )
                result = orchestrator.execute(PipelineConfig(input_path=input_video, run_paths=run_paths, run_id="fail-summarize"))

        assert result.success is False
        assert result.failed_step == failed_step_name
        # Earlier artifacts should still exist
        assert run_paths.microphone_audio.exists()
        if failed_step_name == "summarize":
            assert run_paths.merged_transcript.exists()
