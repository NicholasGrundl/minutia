"""Unit tests for the `minutia config` command and CLI input discovery."""

import pytest
from click.testing import CliRunner

import minutia.cli

pytestmark = pytest.mark.unit


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # keep repo-level .env files out of the layers
    return CliRunner()


def test_config_command_shows_values_and_sources(runner, tmp_path):
    env = {
        "MINUTIA_WHISPER_MODEL": "medium.en",
        "MINUTIA_OUTPUT_DIR": str(tmp_path / "out"),
    }
    result = runner.invoke(minutia.cli.main, ["config"], env=env)
    assert result.exit_code == 0, result.output
    assert "whisper_model = medium.en  [environment]" in result.output
    assert "mic_track = 3  [default]" in result.output
    assert "recordings_dir = <unset>" in result.output
    assert "precedence:" in result.output


def test_process_all_without_input_and_without_recordings_dir_errors(runner, tmp_path):
    env = {"MINUTIA_OUTPUT_DIR": str(tmp_path / "out")}
    result = runner.invoke(minutia.cli.main, ["process-all"], env=env)
    assert result.exit_code != 0
    assert "MINUTIA_RECORDINGS_DIR" in result.output
