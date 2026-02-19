"""Shared pytest fixtures for the minutia test suite.

This module provides reusable fixtures following pytest best practices:
https://docs.pytest.org/en/stable/how-to/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

import json
from pathlib import Path

import pytest

from minutia.paths import RunPaths
from minutia.pipeline.orchestrator import PipelineConfig

# Import mocks to register them as fixtures
from tests.mocks.ffmpeg_mock import mock_ffmpeg, dummy_wav
from tests.mocks.whisper_mock import mock_whisper
from tests.mocks.llm_mock import mock_llm
from tests.mocks.chaos_config import chaos_config

# Session-scoped fixtures for expensive resources

@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_scenarios(test_fixtures_dir):
    """Load test scenarios from the scenarios directory."""
    scenarios_dir = test_fixtures_dir / "scenarios"
    scenarios = {}
    if scenarios_dir.exists():
        for scenario_dir in scenarios_dir.iterdir():
            if scenario_dir.is_dir():
                scenarios[scenario_dir.name] = scenario_dir
    return scenarios


@pytest.fixture
def scenario_loader(test_scenarios, mock_whisper, mock_llm, mock_ffmpeg):
    """
    Helper to load a specific scenario and configure mocks accordingly.
    """
    def _load(name: str):
        scenario_path = test_scenarios.get(name)
        if not scenario_path:
            pytest.fail(f"Scenario '{name}' not found in {test_scenarios.keys()}")
        
        metadata_path = scenario_path / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            # Configure mocks based on metadata if needed
            # For now, we'll just return the path and metadata
            return {"path": scenario_path, "metadata": metadata}
        return {"path": scenario_path, "metadata": {}}

    return _load


@pytest.fixture(scope="session")
def golden_samples(test_fixtures_dir):
    """Load golden sample outputs for regression testing."""
    golden_dir = test_fixtures_dir / "golden_samples"
    samples = {}
    if golden_dir.exists():
        for sample_dir in golden_dir.iterdir():
            if sample_dir.is_dir():
                samples[sample_dir.name] = sample_dir
    return samples


@pytest.fixture
def isolated_tmp_dir(tmp_path):
    """Create isolated temporary directory for each test."""
    return tmp_path


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API for unit/integration tests."""
    # TODO: Implement proper Anthropic API mocking
    pass


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
        sample_video_file,
        base_output_dir=tmp_path / "runs"
    )


@pytest.fixture
def sample_pipeline_config(sample_run_paths):
    """Create a basic PipelineConfig for testing.

    Provides a valid PipelineConfig with sensible defaults for most tests.
    Tests can override specific fields as needed.
    """
    return PipelineConfig(
        input_path=sample_run_paths.input_path,
        run_paths=sample_run_paths,
        run_id="test-run-id",
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


@pytest.fixture
def sample_personal_notes(tmp_path):
    """Create sample personal notes files for testing.

    Returns a dict with 'json' and 'markdown' keys pointing to Path objects
    of sample notes files that can be used in pipeline testing.
    """
    json_notes = tmp_path / "personal_notes.json"
    markdown_notes = tmp_path / "notes.md"

    json_content = [
        {
            "note": "Follow up with team on action items",
            "bullets": ["Send meeting recap", "Schedule follow-up"]
        },
        {
            "note": "Technical requirements discussion",
            "bullets": ["Review architecture", "Finalize timeline"]
        }
    ]

    markdown_content = """# Meeting Context

## Background
Important context for this meeting.

## Key Topics
- Technical architecture
- Timeline and milestones
- Resource allocation
"""

    json_notes.write_text(json.dumps(json_content), encoding="utf-8")
    markdown_notes.write_text(markdown_content, encoding="utf-8")

    return {
        "json": json_notes,
        "markdown": markdown_notes,
    }


# Factory fixtures for more complex scenarios

@pytest.fixture
def run_paths_factory(tmp_path):
    """Factory fixture to create multiple RunPaths instances.

    Useful for tests that need multiple different RunPaths configurations.

    Usage:
        def test_multiple_runs(run_paths_factory):
            run1 = run_paths_factory("meeting1.mkv")
            run2 = run_paths_factory("meeting2.mkv")
    """
    def _create_run_paths(video_filename: str, **kwargs):
        video_file = tmp_path / video_filename
        video_file.write_text("video-content", encoding="utf-8")
        base_output_dir = kwargs.get("base_output_dir", tmp_path / "runs")
        return RunPaths.from_video_input(video_file, base_output_dir=base_output_dir)

    return _create_run_paths


@pytest.fixture
def pipeline_config_factory(run_paths_factory):
    """Factory fixture to create PipelineConfig instances with custom settings.

    Usage:
        def test_custom_config(pipeline_config_factory):
            config = pipeline_config_factory(
                whisper_model="large",
                summary_model="claude-3-haiku"
            )
    """
    def _create_config(video_filename: str = "test.mkv", **overrides):
        run_paths = run_paths_factory(video_filename)
        base_config = {
            "input_path": run_paths.input_path,
            "run_paths": run_paths,
            "run_id": "factory-test-run",
        }
        base_config.update(overrides)
        return PipelineConfig(**base_config)

    return _create_config
