"""Demonstration of conftest.py fixture usage patterns.

This file showcases how to use the shared fixtures defined in conftest.py.
You can delete this file after reviewing the patterns - it's just for demonstration.
"""

import pytest
from minutia.pipeline import PipelineConfig


def test_using_basic_fixtures(sample_video_file, sample_run_paths):
    """Demonstrates using the basic shared fixtures."""
    # sample_video_file provides a Path to a temporary .mkv file
    assert sample_video_file.name == "meeting.mkv"
    assert sample_video_file.exists()
    
    # sample_run_paths provides a configured RunPaths instance
    assert sample_run_paths.input_path == sample_video_file.resolve()
    assert sample_run_paths.run_root.parent.name == "runs"


def test_using_transcript_fixtures(sample_transcript_json, sample_legacy_transcript):
    """Demonstrates transcript-related fixtures."""
    # sample_transcript_json provides mic/desktop JSON transcript files
    mic_path = sample_transcript_json["microphone"]
    desktop_path = sample_transcript_json["desktop"]
    
    assert mic_path.exists()
    assert desktop_path.exists()
    assert "microphone" in mic_path.name
    assert "desktop" in desktop_path.name
    
    # sample_legacy_transcript provides a legacy format transcript
    assert sample_legacy_transcript.exists()
    content = sample_legacy_transcript.read_text()
    assert "[0.00 - 1.00]" in content


def test_using_pipeline_config_fixture(sample_pipeline_config):
    """Demonstrates the pipeline config fixture."""
    assert sample_pipeline_config.run_id == "test-run-id"
    assert sample_pipeline_config.whisper_model == "base"  # default
    assert sample_pipeline_config.summary_model == "claude-4-5-sonnet"  # default


def test_using_notes_fixtures(sample_personal_notes):
    """Demonstrates personal notes fixtures."""
    json_notes = sample_personal_notes["json"]
    markdown_notes = sample_personal_notes["markdown"]
    
    assert json_notes.exists()
    assert markdown_notes.exists()
    assert json_notes.suffix == ".json"
    assert markdown_notes.suffix == ".md"


def test_using_factory_fixtures(run_paths_factory, pipeline_config_factory):
    """Demonstrates factory fixtures for creating multiple instances."""
    # Create multiple RunPaths instances with different video files
    run1 = run_paths_factory("meeting1.mkv")
    run2 = run_paths_factory("meeting2.mkv")
    
    assert run1.input_path.name == "meeting1.mkv"
    assert run2.input_path.name == "meeting2.mkv"
    assert run1.run_root != run2.run_root  # Different directories
    
    # Create custom pipeline configs
    config1 = pipeline_config_factory(
        video_filename="custom.mkv",
        whisper_model="large",
        summary_model="claude-3-haiku"
    )
    
    assert config1.whisper_model == "large"
    assert config1.summary_model == "claude-3-haiku"
    assert config1.input_path.name == "custom.mkv"


@pytest.mark.parametrize("model,expected_default", [
    ("base", "claude-4-5-sonnet"),
    ("large", "claude-4-5-sonnet"),
])
def test_parametrized_with_factory(pipeline_config_factory, model, expected_default):
    """Demonstrates combining parametrization with factory fixtures."""
    config = pipeline_config_factory(whisper_model=model)
    
    assert config.whisper_model == model
    assert config.summary_model == expected_default


def test_combining_fixtures(sample_run_paths, sample_transcript_json, tmp_path):
    """Demonstrates using multiple fixtures together."""
    # You can combine shared fixtures with pytest built-ins like tmp_path
    mic_path = sample_transcript_json["microphone"] 
    
    # Create a new file in tmp_path that references existing fixtures
    summary_file = tmp_path / "summary.txt"
    summary_file.write_text(f"Processed {sample_run_paths.input_path.name}")
    
    assert summary_file.exists()
    assert "meeting.mkv" in summary_file.read_text()
    assert mic_path.exists()  # From sample_transcript_json fixture