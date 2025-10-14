import json
from pathlib import Path

from minutia import (
    audio_transcription,
    baseline_pipeline,
    summarize_transcript,
    video_extraction,
)


def test_baseline_pipeline_smoke(tmp_path, monkeypatch):
    # Arrange fixture files
    input_video = tmp_path / "sample.mkv"
    input_video.write_text("fake-video", encoding="utf-8")

    personal_notes_file = tmp_path / "notes.json"
    personal_notes_file.write_text(
        json.dumps([{"note": "Follow up with team", "bullets": ["Send recap"]}]),
        encoding="utf-8",
    )

    markdown_notes_file = tmp_path / "notes.md"
    markdown_notes_file.write_text("# Extra context\nDetails go here.\n", encoding="utf-8")

    created_transcripts = []

    def fake_process_mkv_file(input_mkv: str, output_dir: str, **kwargs):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        microphone = out_dir / "microphone_audio.wav"
        desktop = out_dir / "desktop_audio.wav"
        microphone.write_text("mic-bytes", encoding="utf-8")
        desktop.write_text("desktop-bytes", encoding="utf-8")
        return {"microphone": str(microphone), "desktop": str(desktop)}

    def fake_process_audio_files(mic_audio, desktop_audio, output_dir, whisper_model_name="base"):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        mic_transcript = out_dir / "microphone-whisper-fake_transcription.txt"
        desk_transcript = out_dir / "desktop-whisper-fake_transcription.txt"
        mic_transcript.write_text("[0.00 - 1.00] Hello from mic\n", encoding="utf-8")
        desk_transcript.write_text("[0.25 - 1.25] Hello from desktop\n", encoding="utf-8")
        created_transcripts.append((mic_transcript, desk_transcript))
        return {"microphone": str(mic_transcript), "desktop": str(desk_transcript)}

    def fake_estimate(transcript_text, model="claude-3-5-sonnet", max_output_tokens=None):
        return 256, 0.42

    def fake_generate_summary(transcript_text, model_name="claude-3-5-sonnet", **kwargs):
        assert "Hello from mic" in transcript_text
        return "Summary content"

    def fake_save_summary(summary, output_file):
        Path(output_file).write_text(summary, encoding="utf-8")

    def fake_create_markdown(content, output_path, model_name="claude-3-5-sonnet"):
        markdown_path = output_path / "meeting_summary.md"
        markdown_path.write_text(content, encoding="utf-8")
        return markdown_path

    monkeypatch.setattr(video_extraction, "process_mkv_file", fake_process_mkv_file)
    monkeypatch.setattr(audio_transcription, "process_audio_files", fake_process_audio_files)
    monkeypatch.setattr(
        summarize_transcript, "estimate_tokens_and_price", fake_estimate, raising=False
    )
    monkeypatch.setattr(
        summarize_transcript, "generate_summary", fake_generate_summary, raising=False
    )
    monkeypatch.setattr(
        summarize_transcript, "generate_long_summary", fake_generate_summary, raising=False
    )
    monkeypatch.setattr(summarize_transcript, "save_summary", fake_save_summary, raising=False)
    monkeypatch.setattr(baseline_pipeline, "create_markdown_report", fake_create_markdown)
    monkeypatch.setenv("MINUTIA_ANTHROPIC_API_KEY", "test-key")

    args = baseline_pipeline.build_parser().parse_args(
        [
            str(input_video),
            "--output-dir",
            str(tmp_path / "runs"),
            "--summary-filename",
            "summary.txt",
            "--summary-model",
            "claude-3-5-sonnet",
            "--generate-markdown",
            "--personal-notes",
            str(personal_notes_file),
            "--personal-info",
            "Product manager with TEA focus",
            "--markdown-notes",
            str(markdown_notes_file),
            "--parse-overlaps",
        ]
    )

    artifacts = baseline_pipeline.run_pipeline(args)

    # Validate audio extraction and transcription steps
    assert created_transcripts, "Transcription step did not create transcripts"
    assert artifacts.run_paths.audio_dir.exists()
    assert artifacts.transcription_files["microphone"].exists()

    # Validate merged transcript file
    assert artifacts.merged_transcript.exists()
    merged_data = json.loads(artifacts.merged_transcript.read_text(encoding="utf-8"))
    assert merged_data["metadata"]["segment_count"] > 0

    # Validate summary artifact
    assert artifacts.summary_file is not None
    assert artifacts.summary_file.read_text(encoding="utf-8") == "Summary content"

    # Validate markdown artifact
    assert artifacts.markdown_file is not None
    assert artifacts.markdown_file.read_text(encoding="utf-8") == "Summary content"
