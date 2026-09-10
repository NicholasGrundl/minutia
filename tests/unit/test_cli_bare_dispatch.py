"""Unit tests for bare `minutia` self-determination + the `setup` command.

Bare ``minutia`` runs the callback (``invoke_without_command=True``) and, with no subcommand,
dispatches: configured → guided run; unconfigured → setup, then (if not cancelled) guided. The
wizard flows are patched on the ``minutia.cli.wizard`` package — where the callback's lazy
``from .wizard import ...`` resolves them at call time.
"""

import pytest
from click.testing import CliRunner

import minutia.cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return CliRunner()


def _spy(calls, name, result=None):
    def fn(config, **kwargs):
        calls.append(name)
        return result

    return fn


def _configured_env(tmp_path):
    rec = tmp_path / "recordings"
    rec.mkdir(exist_ok=True)
    return {
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "MINUTIA_RECORDINGS_DIR": str(rec),
        "MINUTIA_OUTPUT_DIR": str(tmp_path / "out"),
    }


def test_bare_configured_runs_guided(runner, tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("minutia.cli.wizard.run_guided", _spy(calls, "guided"))
    monkeypatch.setattr("minutia.cli.wizard.run_setup", _spy(calls, "setup", True))
    result = runner.invoke(minutia.cli.main, [], env=_configured_env(tmp_path))
    assert result.exit_code == 0, result.output
    assert calls == ["guided"]


def test_bare_unconfigured_runs_setup_then_cancels(runner, tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("minutia.cli.wizard.run_guided", _spy(calls, "guided"))
    monkeypatch.setattr("minutia.cli.wizard.run_setup", _spy(calls, "setup", False))  # cancelled
    env = {"MINUTIA_OUTPUT_DIR": str(tmp_path / "out")}  # no key, no recordings dir
    result = runner.invoke(minutia.cli.main, [], env=env)
    assert result.exit_code == 0, result.output
    assert calls == ["setup"]  # cancel → guided not reached


def test_bare_unconfigured_setup_completes_then_runs_guided(runner, tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("minutia.cli.wizard.run_guided", _spy(calls, "guided"))
    monkeypatch.setattr("minutia.cli.wizard.run_setup", _spy(calls, "setup", True))
    env = {"MINUTIA_OUTPUT_DIR": str(tmp_path / "out")}
    result = runner.invoke(minutia.cli.main, [], env=env)
    assert result.exit_code == 0, result.output
    assert calls == ["setup", "guided"]


def test_setup_command_runs_setup_unconditionally(runner, tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("minutia.cli.wizard.run_guided", _spy(calls, "guided"))
    monkeypatch.setattr("minutia.cli.wizard.run_setup", _spy(calls, "setup", True))
    # Even fully configured, `minutia setup` runs setup and does NOT launch the guided run.
    result = runner.invoke(minutia.cli.main, ["setup"], env=_configured_env(tmp_path))
    assert result.exit_code == 0, result.output
    assert calls == ["setup"]
