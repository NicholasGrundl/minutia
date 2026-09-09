import pytest

from minutia.steps import (
    audio_transcription,
    summarize_transcript,
    video_extraction,
)


def test_ffmpeg_mock_sanity(mock_ffmpeg, tmp_path):
    # Setup
    input_file = tmp_path / "input.mkv"
    output_file = tmp_path / "output.wav"

    # Execute
    video_extraction.extract_audio_track(input_file, output_file, 0)

    # Verify
    assert output_file.exists()
    assert len(mock_ffmpeg.calls) == 1


def test_whisper_mock_sanity(mock_whisper, tmp_path):
    # Setup
    audio_path = tmp_path / "test.wav"
    audio_path.write_bytes(b"dummy data")

    mock_whisper.set_scenario(
        "test.wav", [{"id": 0, "start": 0.0, "end": 1.0, "text": "Hello world"}]
    )

    # Execute
    result = audio_transcription.transcribe_audio(str(audio_path))

    # Verify
    assert result["text"] == "Hello world"
    assert len(mock_whisper.calls) == 1


def test_llm_mock_sanity(mock_llm):
    # Setup
    mock_llm.set_responses(["Part 1 [CONTINUE]", "Part 2"])

    # Execute
    # generate_long_summary handles the loop
    summary = summarize_transcript.generate_long_summary(
        "dummy transcript", api_key="fake-api-key"
    )

    # Verify
    assert summary == "Part 1 Part 2"
    assert len(mock_llm.calls) == 2


def test_chaos_mock_sanity(mock_ffmpeg, chaos_config, tmp_path):
    # Setup
    input_file = tmp_path / "input.mkv"

    chaos_config.set_failure("ffmpeg.probe", RuntimeError("FFmpeg crashed!"))

    # Execute & Verify
    with pytest.raises(RuntimeError, match="FFmpeg crashed!"):
        video_extraction.get_video_info(input_file)
