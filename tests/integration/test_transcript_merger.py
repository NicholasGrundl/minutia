from __future__ import annotations

import json

import pytest

from minutia import transcript_merger

GOLDEN_SCENARIOS = [
    "microphone_only",
    "noisy_microphone",
    "podcast_desktop",
    "youtube_desktop",
]

# Metadata keys that must survive regeneration; the rest (source paths,
# processed_at timestamps, per-source blocks) legitimately vary per run.
STABLE_METADATA_KEYS = (
    "schema_version",
    "parse_overlaps",
    "segment_count",
    "total_duration",
)


@pytest.mark.integration
@pytest.mark.parametrize("scenario", GOLDEN_SCENARIOS)
def test_merger_reproduces_golden_fixture(scenario, test_scenarios, tmp_path):
    """Merging the 02_transcribed fixtures must reproduce the 03_merged golden."""
    base = test_scenarios[scenario]
    golden = json.loads(
        (base / "03_merged" / "merged_transcript.json").read_text(encoding="utf-8")
    )

    merged = transcript_merger.process_transcripts(
        mic_transcript_file=str(
            base / "02_transcribed" / "microphone-whisper-medium.en_transcription.json"
        ),
        desktop_transcript_file=str(
            base / "02_transcribed" / "desktop-whisper-medium.en_transcription.json"
        ),
        output_file=str(tmp_path / "merged_transcript.json"),
        parse_overlaps=False,
    )

    assert merged["transcript"] == golden["transcript"]
    for key in STABLE_METADATA_KEYS:
        assert merged["metadata"][key] == golden["metadata"][key], key


def test_parse_transcript_supports_legacy_format(sample_legacy_transcript) -> None:
    legacy_file = sample_legacy_transcript

    parsed = transcript_merger.parse_transcript(legacy_file)

    assert parsed["segments"][0]["text"] == "Hello from legacy format"
    assert parsed["segments"][0]["start_time"] == 0.0
    assert parsed["metadata"]["schema_version"] == transcript_merger.SCHEMA_VERSION


def test_merge_transcripts_metadata_includes_sources(
    sample_transcript_json, tmp_path
) -> None:
    mic_path = sample_transcript_json["microphone"]
    desk_path = sample_transcript_json["desktop"]

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
    assert metadata["segment_count"] == 4
