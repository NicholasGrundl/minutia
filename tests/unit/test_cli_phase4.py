"""Unit tests for Phase 4 CLI parity: summarize upgrade, idempotency, minutia go."""

import json

import pytest
from click.testing import CliRunner

import minutia.cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # keep repo .env files out of config layers
    return CliRunner()


@pytest.fixture
def merged_transcript(tmp_path):
    path = tmp_path / "merged_transcript.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {},
                "transcript": [
                    {
                        "source": "microphone",
                        "start_time": 1.0,
                        "end_time": 2.0,
                        "text": "Hello there",
                    },
                    {
                        "source": "desktop",
                        "start_time": 0.0,
                        "end_time": 1.0,
                        "text": "Earlier line",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _env(tmp_path, **extra):
    env = {
        "MINUTIA_OUTPUT_DIR": str(tmp_path / "out"),
        "ANTHROPIC_API_KEY": "fake-key-for-tests",
    }
    env.update(extra)
    return env


class TestSummarize:
    def test_dry_run_estimates_only(
        self, runner, merged_transcript, tmp_path, mock_llm
    ):
        result = runner.invoke(
            minutia.cli.main,
            ["run", "summarize", str(merged_transcript), "--dry-run"],
            env=_env(tmp_path),
        )
        assert result.exit_code == 0, result.output
        assert "Estimated tokens:" in result.output
        assert "Dry run completed" in result.output
        assert mock_llm.calls == []

    def test_generates_report_with_prompt_kind_and_notes(
        self, runner, merged_transcript, tmp_path, mock_llm
    ):
        notes = tmp_path / "notes.md"
        notes.write_text("Speaker map: desktop=Alice", encoding="utf-8")
        info = tmp_path / "me.md"
        info.write_text("Nick is a consultant", encoding="utf-8")
        mock_llm.set_responses(["A summary body.", "20260702_meeting_report"])

        result = runner.invoke(
            minutia.cli.main,
            [
                "run",
                "summarize",
                str(merged_transcript),
                str(tmp_path / "reports"),
                "--prompt-kind",
                "interview-debrief",
                "--notes",
                str(notes),
                "--personal-info",
                str(info),
                "--yes",
            ],
            env=_env(tmp_path),
        )
        assert result.exit_code == 0, result.output
        report = tmp_path / "reports" / "20260702_meeting_report.md"
        assert report.exists()
        assert report.read_text(encoding="utf-8") == "A summary body."
        # First call is the summary: system prompt must carry kind + injected context;
        # transcript must be timestamped-format.
        summary_call = mock_llm.calls[0]
        assert "Interview Debrief" in summary_call["system"]
        assert "Speaker map: desktop=Alice" in summary_call["system"]
        assert "Nick is a consultant" in summary_call["system"]
        assert "[Desktop 0.00] Earlier line" in summary_call["messages"][0]["content"]

    def test_confirmation_declined_aborts_without_api_call(
        self, runner, merged_transcript, tmp_path, mock_llm
    ):
        result = runner.invoke(
            minutia.cli.main,
            ["run", "summarize", str(merged_transcript)],
            env=_env(tmp_path),
            input="n\n",
        )
        assert result.exit_code != 0
        assert mock_llm.calls == []

    def test_unknown_prompt_kind_rejected(self, runner, merged_transcript, tmp_path):
        result = runner.invoke(
            minutia.cli.main,
            ["run", "summarize", str(merged_transcript), "--prompt-kind", "nope"],
            env=_env(tmp_path),
        )
        assert result.exit_code != 0


class TestIdempotency:
    def test_extract_audio_skips_when_outputs_exist(
        self, runner, tmp_path, monkeypatch
    ):
        video = tmp_path / "meeting.mkv"
        video.write_text("video", encoding="utf-8")
        out = tmp_path / "out"
        out.mkdir()
        (out / "microphone_audio.wav").write_text("m", encoding="utf-8")
        (out / "desktop_audio.wav").write_text("d", encoding="utf-8")

        def boom(*args, **kwargs):
            raise AssertionError("process_mkv_file should not be called")

        monkeypatch.setattr("minutia.steps.video_extraction.process_mkv_file", boom)
        result = runner.invoke(
            minutia.cli.main,
            ["run", "extract-audio", str(video), str(out)],
            env=_env(tmp_path),
        )
        assert result.exit_code == 0, result.output
        assert "skipping extraction" in result.output

    def test_transcribe_skips_when_outputs_exist(self, runner, tmp_path, monkeypatch):
        out = tmp_path / "out"
        out.mkdir()
        mic = out / "microphone_audio.wav"
        desk = out / "desktop_audio.wav"
        mic.write_text("m", encoding="utf-8")
        desk.write_text("d", encoding="utf-8")
        for kind in ("microphone", "desktop"):
            (out / f"{kind}-whisper-base_transcription.json").write_text(
                "{}", encoding="utf-8"
            )

        def boom(*args, **kwargs):
            raise AssertionError("process_audio_files should not be called")

        monkeypatch.setattr("minutia.steps.audio_transcription.process_audio_files", boom)
        result = runner.invoke(
            minutia.cli.main,
            ["run", "transcribe", str(mic), str(desk), str(out)],
            env=_env(tmp_path, MINUTIA_WHISPER_MODEL="base"),
        )
        assert result.exit_code == 0, result.output
        assert "skipping" in result.output


class TestResolveNotesAnswer:
    """`_resolve_notes_answer` takes inline text OR a file path (reused by the guided wizard)."""

    def test_blank_returns_none(self, tmp_path):
        assert minutia.cli._steps._resolve_notes_answer("", tmp_path) is None
        assert minutia.cli._steps._resolve_notes_answer("   ", tmp_path) is None

    def test_existing_file_is_used_as_path(self, tmp_path):
        notes = tmp_path / "my_notes.md"
        notes.write_text("desktop=Alice", encoding="utf-8")
        result = minutia.cli._steps._resolve_notes_answer(str(notes), tmp_path)
        assert result == notes
        # a real path must not spawn an inline notes.md
        assert not (tmp_path / "notes.md").exists()

    def test_inline_text_is_persisted_to_notes_md(self, tmp_path):
        out = tmp_path / "run"
        out.mkdir()
        text = "microphone track is Nick Grundl, desktop track is client"
        result = minutia.cli._steps._resolve_notes_answer(text, out)
        assert result is not None
        assert result == out / "notes.md"
        assert result.read_text(encoding="utf-8") == text + "\n"
