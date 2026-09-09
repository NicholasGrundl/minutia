import json

from minutia import baseline_pipeline


def test_baseline_pipeline_smoke(tmp_path, mock_ffmpeg, mock_whisper, mock_llm):
    # Arrange fixture files
    input_video = tmp_path / "sample.mkv"
    input_video.write_text("fake-video", encoding="utf-8")

    personal_notes_file = tmp_path / "notes.json"
    personal_notes_file.write_text(
        json.dumps([{"note": "Follow up with team", "bullets": ["Send recap"]}]),
        encoding="utf-8",
    )

    markdown_notes_file = tmp_path / "notes.md"
    markdown_notes_file.write_text(
        "# Extra context\nDetails go here.\n", encoding="utf-8"
    )

    # Configure Mocks
    mock_ffmpeg.set_probe_data(input_video, audio_tracks=3)

    # Set scenarios for whisper mock to return specific text
    mock_whisper.set_scenario(
        "microphone_audio", [{"start": 0.0, "end": 1.0, "text": "Hello from mic"}]
    )
    mock_whisper.set_scenario(
        "desktop_audio", [{"start": 0.25, "end": 1.25, "text": "Hello from desktop"}]
    )

    # Configure LLM mock responses
    mock_llm.set_responses(["Summary content"])

    # Run the pipeline
    args = baseline_pipeline.build_parser().parse_args(
        [
            str(input_video),
            "--output-dir",
            str(tmp_path / "runs"),
            "--summary-filename",
            "summary.txt",
            "--summary-model",
            "claude-sonnet-4-6",
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
    assert artifacts.run_paths.audio_dir.exists()
    assert artifacts.transcription_files["microphone"].exists()

    # Validate merged transcript file
    assert artifacts.merged_transcript.exists()
    merged_data = json.loads(artifacts.merged_transcript.read_text(encoding="utf-8"))
    assert merged_data["metadata"]["segment_count"] > 0
    assert "microphone" in merged_data["metadata"]["source_files"]

    # Validate summary artifact
    assert artifacts.summary_file is not None
    assert artifacts.summary_file.read_text(encoding="utf-8") == "Summary content"

    # Validate markdown artifact
    assert artifacts.markdown_file is not None
    assert artifacts.markdown_file.read_text(encoding="utf-8") == "Summary content"

    # Validate run metadata artifact
    metadata_file = artifacts.run_paths.metadata_file
    assert metadata_file.exists()
    run_metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert run_metadata["run_info"]["status"] == "completed"
