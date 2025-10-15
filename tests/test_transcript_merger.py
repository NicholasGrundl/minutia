from __future__ import annotations

import json
from pathlib import Path

from minutia import transcript_merger


def test_parse_transcript_supports_legacy_format(tmp_path: Path) -> None:
    legacy_file = tmp_path / "microphone_transcript.txt"
    legacy_file.write_text("[0.00 - 1.00] Hello legacy\n", encoding="utf-8")

    parsed = transcript_merger.parse_transcript(legacy_file)

    assert parsed["segments"][0]["text"] == "Hello legacy"
    assert parsed["segments"][0]["start_time"] == 0.0
    assert parsed["metadata"]["schema_version"] == transcript_merger.SCHEMA_VERSION


def test_merge_transcripts_metadata_includes_sources(tmp_path: Path) -> None:
    mic_path = tmp_path / "microphone.json"
    desk_path = tmp_path / "desktop.json"
    mic_payload = {
        "metadata": {"source_file": str(mic_path), "schema_version": "1.0"},
        "segments": [{"start_time": 0.0, "end_time": 1.0, "text": "Mic"}],
    }
    desk_payload = {
        "metadata": {"source_file": str(desk_path), "schema_version": "1.0"},
        "segments": [{"start_time": 0.5, "end_time": 1.5, "text": "Desk"}],
    }
    mic_path.write_text(json.dumps(mic_payload), encoding="utf-8")
    desk_path.write_text(json.dumps(desk_payload), encoding="utf-8")

    output_path = tmp_path / "merged.json"
    merged = transcript_merger.process_transcripts(
        mic_transcript_file=str(mic_path),
        desktop_transcript_file=str(desk_path),
        output_file=str(output_path),
        parse_overlaps=False,
    )

    assert output_path.exists()
    metadata = merged["metadata"]
    assert metadata["schema_version"] == transcript_merger.SCHEMA_VERSION
    assert metadata["source_files"]["microphone"] == str(mic_path)
    assert metadata["source_files"]["desktop"] == str(desk_path)
    assert metadata["segment_count"] == 2
