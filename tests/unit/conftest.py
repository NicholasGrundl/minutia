import pytest

from minutia.paths import RunPaths


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
    return RunPaths.from_video_input(
        sample_video_file, base_output_dir=tmp_path / "runs"
    )
