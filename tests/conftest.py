"""Shared pytest fixtures for the minutia test suite.

This module provides reusable fixtures following pytest best practices:
https://docs.pytest.org/en/stable/how-to/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

import json
import os
from pathlib import Path

import pytest

from minutia.paths import RunPaths
from minutia.pipeline.orchestrator import PipelineConfig

pytest_plugins = (
    "tests.mocks.chaos_config",
    "tests.mocks.ffmpeg_mock",
    "tests.mocks.llm_mock",
    "tests.mocks.whisper_mock",
)

# Tier == directory: this is the single source of truth for the unit /
# integration / slow markers. Files carry no per-file `pytestmark`; putting a
# test in the right directory is all that's needed. Kills the marker-drift class.
_TIER_DIRS = {"unit", "integration", "slow"}


def pytest_collection_modifyitems(config, items):
    """Auto-apply the tier marker from each test's top-level directory."""
    tests_root = Path(__file__).parent
    for item in items:
        try:
            rel = item.path.relative_to(tests_root)
        except ValueError:
            continue
        top = rel.parts[0] if rel.parts else ""
        if top in _TIER_DIRS:
            item.add_marker(getattr(pytest.mark, top))


@pytest.fixture(autouse=True)
def _scrub_minutia_environment(monkeypatch):
    """Keep tests independent from developer and previously loaded settings."""
    for key in tuple(os.environ):
        if key.startswith("MINUTIA_") or key in {
            "ANTHROPIC_API_KEY",
            "CLAUDE_API_KEY",
        }:
            monkeypatch.delenv(key)


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
