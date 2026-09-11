"""Integration tests for the `minutia run` command group.

`run pipeline` executes the whole pipeline non-interactively on the shared step helpers (never the
orchestrator). Here we mock the three step source functions + the Anthropic client (`mock_llm`) and
assert the pipeline chains end to end and writes the report. The individual `run <step>` subcommands
are covered in tests/unit/test_cli_phase4.py.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

import minutia.cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # keep repo .env files out of config layers
    return CliRunner()


def test_run_all_chains_pipeline_and_writes_report(
    runner, tmp_path, monkeypatch, mocker, mock_llm
):
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    (recordings / "meeting.mkv").write_text("v", encoding="utf-8")

    out_root = tmp_path / "out"
    workdir = out_root / "meeting"  # run-all writes to <output_dir>/<recording stem>

    def fake_extract(input_video, output_dir, **kwargs):
        for name in ("microphone_audio.wav", "desktop_audio.wav"):
            (workdir / name).write_text("wav", encoding="utf-8")
        return {"microphone": "m", "desktop": "d"}

    def fake_transcribe(mic, desk, output_dir, **kwargs):
        paths = {}
        for kind in ("microphone", "desktop"):
            p = workdir / f"{kind}-whisper-base_transcription.json"
            p.write_text("{}", encoding="utf-8")
            paths[kind] = str(p)
        return paths

    def fake_merge(mic_transcript_file, desktop_transcript_file, output_file, **kwargs):
        data = {
            "metadata": {},
            "transcript": [
                {
                    "source": "microphone",
                    "start_time": 0.0,
                    "end_time": 1.0,
                    "text": "hi",
                }
            ],
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data

    # Lazy imports resolve step functions in their source modules — patch them there.
    monkeypatch.setattr("minutia.steps.video_extraction.process_mkv_file", fake_extract)
    monkeypatch.setattr(
        "minutia.steps.audio_transcription.process_audio_files", fake_transcribe
    )
    monkeypatch.setattr(
        "minutia.steps.transcript_merger.process_transcripts", fake_merge
    )
    mock_llm.set_responses(["Run-all summary.", "20260702_run_report"])

    # Give the run a concrete resolved settings object (overrides mock_llm's MagicMock config).
    from minutia.config import MinutiaSettings, SettingsResolution

    settings = MinutiaSettings(
        whisper_model="base",
        recordings_dir=recordings,
        base_output_dir=out_root,
        anthropic_api_key="fake-key-for-tests",
    )
    resolution = SettingsResolution(
        settings=settings,
        sources={},
        invocation_dir=tmp_path,
        context_env_file=None,
        user_config_file=tmp_path / "config.env",
    )
    # Override resolve_settings via `mocker` (not `monkeypatch`): mock_llm already patched it, and
    # a monkeypatch here would capture that mock as its "original" and re-install it at teardown
    # (monkeypatch tears down after mock_llm), leaking the mock into later tests. One mocker stack
    # unwinds correctly.
    mocker.patch("minutia.cli.app.resolve_settings", return_value=resolution)

    result = runner.invoke(
        minutia.cli.main,
        ["run", "pipeline", "--yes"],  # --yes skips the summarize cost confirmation
        env={"ANTHROPIC_API_KEY": "fake-key-for-tests"},
    )
    assert result.exit_code == 0, result.output
    assert "Working in:" in result.output
    report = workdir / "20260702_run_report.md"
    assert report.exists()
    assert report.read_text(encoding="utf-8") == "Run-all summary."
