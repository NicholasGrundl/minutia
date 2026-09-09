"""Unit tests for the `minutia config` command and CLI input discovery."""

import os

import pytest
from click.testing import CliRunner

import minutia.cli
from minutia import config as config_module

pytestmark = pytest.mark.unit


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        config_module, "USER_CONFIG_FILE", tmp_path / "user-config" / "config.env"
    )
    for key in list(os.environ):
        if key.startswith("MINUTIA_") or key in {
            "ANTHROPIC_API_KEY",
            "CLAUDE_API_KEY",
        }:
            monkeypatch.delenv(key)
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
    assert f"invocation directory: {tmp_path}" in result.output
    assert "contextual env file: <none>" in result.output
    assert "precedence:" in result.output


def test_process_all_without_input_and_without_recordings_dir_errors(runner, tmp_path):
    env = {"MINUTIA_OUTPUT_DIR": str(tmp_path / "out")}
    result = runner.invoke(minutia.cli.main, ["process-all"], env=env)
    assert result.exit_code != 0
    assert "MINUTIA_RECORDINGS_DIR" in result.output


def test_config_command_discovers_nearest_env_file(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("MINUTIA_WHISPER_MODEL=tiny\n", encoding="utf-8")

    result = runner.invoke(minutia.cli.main, ["config"])

    assert result.exit_code == 0, result.output
    assert f"whisper_model = tiny  [{env_file}]" in result.output
    assert f"contextual env file: {env_file}" in result.output


def test_no_env_file_disables_contextual_discovery(runner, tmp_path):
    (tmp_path / ".env").write_text("MINUTIA_WHISPER_MODEL=tiny\n", encoding="utf-8")

    result = runner.invoke(minutia.cli.main, ["--no-env-file", "config"])

    assert result.exit_code == 0, result.output
    assert "whisper_model = base  [default]" in result.output
    assert "contextual env file: <none>" in result.output


def test_explicit_env_file_bypasses_discovery(runner, tmp_path):
    (tmp_path / ".env").write_text(
        "MINUTIA_WHISPER_MODEL=discovered\n", encoding="utf-8"
    )
    selected = tmp_path / "selected.env"
    selected.write_text("MINUTIA_WHISPER_MODEL=explicit\n", encoding="utf-8")

    result = runner.invoke(minutia.cli.main, ["--env-file", str(selected), "config"])

    assert result.exit_code == 0, result.output
    assert f"whisper_model = explicit  [{selected}]" in result.output


def test_explicit_and_disabled_env_file_are_mutually_exclusive(runner, tmp_path):
    selected = tmp_path / "selected.env"
    selected.touch()

    result = runner.invoke(
        minutia.cli.main,
        ["--env-file", str(selected), "--no-env-file", "config"],
    )

    assert result.exit_code != 0
    assert "cannot be used together" in result.output
