import json

import pytest


@pytest.fixture
def sample_video_file(tmp_path):
    """Create a sample video file for testing.

    Returns a Path object to a temporary .mkv file with dummy content.
    Useful for tests that need video input files.
    """
    video_file = tmp_path / "meeting.mkv"
    video_file.write_text("video-bytes", encoding="utf-8")
    return video_file


@pytest.fixture
def sample_run_paths(sample_video_file, tmp_path):
    """Create a standard RunPaths structure for testing.

    Uses the sample_video_file fixture and creates RunPaths with standard
    output directory structure. This is the most commonly needed fixture
    across multiple test modules.
    """
    from minutia.paths import RunPaths

    return RunPaths.from_video_input(
        sample_video_file, base_output_dir=tmp_path / "runs"
    )


@pytest.fixture
def sample_transcript_json(tmp_path):
    """Create sample transcript JSON files for testing transcript merging.

    Returns a dict with 'microphone' and 'desktop' keys pointing to
    Path objects of JSON transcript files with realistic structure.
    """
    mic_path = tmp_path / "microphone.json"
    desktop_path = tmp_path / "desktop.json"

    mic_data = {
        "metadata": {
            "source_file": str(mic_path),
            "model": "whisper-base",
            "schema_version": "1.0",
            "processed_at": "2024-01-01T00:00:00+00:00",
        },
        "segments": [
            {"start_time": 0.0, "end_time": 1.0, "text": "Hello from microphone"},
            {"start_time": 2.0, "end_time": 3.0, "text": "Second mic segment"},
        ],
        "text": "Hello from microphone Second mic segment",
    }

    desktop_data = {
        "metadata": {
            "source_file": str(desktop_path),
            "model": "whisper-base",
            "schema_version": "1.0",
            "processed_at": "2024-01-01T00:00:00+00:00",
        },
        "segments": [
            {"start_time": 0.5, "end_time": 1.5, "text": "Hello from desktop"},
            {"start_time": 2.5, "end_time": 3.5, "text": "Second desktop segment"},
        ],
        "text": "Hello from desktop Second desktop segment",
    }

    mic_path.write_text(json.dumps(mic_data), encoding="utf-8")
    desktop_path.write_text(json.dumps(desktop_data), encoding="utf-8")

    return {
        "microphone": mic_path,
        "desktop": desktop_path,
    }


@pytest.fixture
def sample_legacy_transcript(tmp_path):
    """Create a sample legacy transcript file for testing backward compatibility.

    Returns a Path to a legacy format transcript file with bracketed timestamps.
    """
    legacy_file = tmp_path / "legacy_transcript.txt"
    legacy_content = """[0.00 - 1.00] Hello from legacy format
[2.50 - 4.00] This is a second segment
[5.00 - 6.50] Final legacy segment
"""
    legacy_file.write_text(legacy_content, encoding="utf-8")
    return legacy_file
