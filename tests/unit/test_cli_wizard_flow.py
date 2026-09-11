"""Unit tests for the wizard flows + their pure cores.

The flows take an injected ``ui``; ``FakeUI`` scripts menu/field answers and runs staged steps
inline (so mocked source functions execute and populate shared state), with no terminal. The heavy
step functions are patched at their **source modules** (where the flow's lazy imports resolve them).
"""

from __future__ import annotations

import pytest

from minutia.cli.wizard import flow, tui
from minutia.config import MinutiaSettings


class _Console:
    def __init__(self):
        self.lines: list[str] = []

    def print(self, *args):
        for arg in args:
            self.lines.append(getattr(arg, "plain", str(arg)))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class FakeUI:
    """A drop-in for the ``tui`` module: scripted answers, inline staged execution, no tty."""

    HeaderStatus = tui.HeaderStatus
    Step = tui.Step

    def __init__(self, *, selects=(), texts=(), notes=()):
        self._selects = list(selects)
        self._texts = list(texts)
        self._notes = list(notes)
        self._console = _Console()

    def console(self):
        return self._console

    def select(self, panes, options, *, cursor_index=0, **kwargs):
        return self._selects.pop(0)

    def prompt_text(self, panes, **kwargs):
        return self._texts.pop(0)

    def prompt_notes(self, panes, **kwargs):
        return self._notes.pop(0)

    def run_staged_progress(self, steps, panes, *, status=None, **kwargs):
        results = []
        for step in steps:
            try:
                results.append(step.run())
            except Exception as error:  # mirror the real StepError contract
                results.append(tui.StepError(step.label, str(error)))
                return results
        return results


# --- Pure cores ---------------------------------------------------------------------------------


class TestPureCores:
    def test_detect_env_api_key_precedence(self):
        assert flow.detect_env_api_key(
            {"ANTHROPIC_API_KEY": "a", "MINUTIA_ANTHROPIC_API_KEY": "b"}
        ) == (
            "ANTHROPIC_API_KEY",
            "a",
        )

    def test_detect_env_api_key_namespaced_only(self):
        assert flow.detect_env_api_key({"MINUTIA_ANTHROPIC_API_KEY": "b"}) == (
            "MINUTIA_ANTHROPIC_API_KEY",
            "b",
        )

    def test_detect_env_api_key_absent(self):
        assert flow.detect_env_api_key({}) is None

    def test_language_of(self):
        assert flow._language_of("medium.en") == "en"
        assert flow._language_of("base") == "multi"


# --- Setup flow ---------------------------------------------------------------------------------


class TestSetupFlow:
    def _config(self, tmp_path):
        return MinutiaSettings(base_output_dir=tmp_path / "out")

    def test_persists_pasted_recordings_dir_and_pasted_key(self, tmp_path):
        cfg_path = tmp_path / "config.env"
        ui = FakeUI(
            selects=[
                1,
                0,
            ],  # recordings: "Paste a folder path"; key: "Paste an API key"
            texts=[str(tmp_path / "videos"), "sk-ant-pasted"],
        )
        ok = flow.run_setup(self._config(tmp_path), ui=ui, env={}, config_path=cfg_path)
        assert ok is True
        body = cfg_path.read_text(encoding="utf-8")
        assert f"MINUTIA_RECORDINGS_DIR={tmp_path / 'videos'}" in body
        assert "MINUTIA_ANTHROPIC_API_KEY=sk-ant-pasted" in body

    def test_uses_default_recordings_and_detected_env_key(self, tmp_path):
        cfg_path = tmp_path / "config.env"
        ui = FakeUI(
            selects=[
                0,
                1,
            ],  # recordings: "Use <default>"; key: "Use ANTHROPIC_API_KEY…"
        )
        ok = flow.run_setup(
            self._config(tmp_path),
            ui=ui,
            env={"ANTHROPIC_API_KEY": "sk-ant-env"},
            config_path=cfg_path,
        )
        assert ok is True
        body = cfg_path.read_text(encoding="utf-8")
        assert "MINUTIA_RECORDINGS_DIR=" in body  # the default was persisted
        assert "MINUTIA_ANTHROPIC_API_KEY=sk-ant-env" in body

    def test_cancel_writes_nothing(self, tmp_path):
        cfg_path = tmp_path / "config.env"
        ui = FakeUI(selects=[None])  # Esc on the recordings menu
        ok = flow.run_setup(self._config(tmp_path), ui=ui, env={}, config_path=cfg_path)
        assert ok is False
        assert not cfg_path.exists()


# --- Guided-run flow ----------------------------------------------------------------------------


@pytest.fixture
def guided_config(tmp_path):
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    (recordings / "standup.mkv").write_text("v", encoding="utf-8")
    return MinutiaSettings(
        whisper_model="base",
        recordings_dir=recordings,
        base_output_dir=tmp_path / "out",
        anthropic_api_key="sk-ant-test",
    )


def _mock_pipeline(monkeypatch, tmp_path, *, report_name="report"):
    """Patch every heavy source function the guided flow calls, at its source module."""
    monkeypatch.setattr(
        "minutia.steps.video_extraction.process_mkv_file",
        lambda *a, **k: {"microphone": "m.wav", "desktop": "d.wav"},
    )
    monkeypatch.setattr(
        "minutia.steps.audio_transcription.process_audio_files",
        lambda *a, **k: {"microphone": "m.json", "desktop": "d.json"},
    )
    monkeypatch.setattr(
        "minutia.steps.transcript_merger.process_transcripts", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        "minutia.steps.summarize_transcript.load_transcript", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        "minutia.steps.summarize_transcript.extract_transcript_text",
        lambda *a, **k: "transcript text",
    )
    monkeypatch.setattr(
        "minutia.steps.summarize_transcript.estimate_tokens_and_price",
        lambda *a, **k: (1234, 0.0456),
    )
    monkeypatch.setattr(
        "minutia.prompts.generate_meeting_summary_prompt", lambda *a, **k: "system"
    )
    monkeypatch.setattr(
        "minutia.steps.summarize_transcript.generate_long_summary",
        lambda *a, **k: "the summary",
    )
    report = tmp_path / "out" / "standup" / f"{report_name}.md"
    monkeypatch.setattr(
        "minutia.steps.summarize_transcript.create_markdown_report",
        lambda *a, **k: report,
    )
    return report


def test_guided_happy_path_runs_and_reports(guided_config, tmp_path, monkeypatch):
    report = _mock_pipeline(monkeypatch, tmp_path)
    from minutia.prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds

    ui = FakeUI(
        selects=[
            0,  # pick recording (standup.mkv)
            list_prompt_kinds().index(DEFAULT_PROMPT_KIND),  # summary style
            2,  # notes: "No notes"
            0,  # confirm: "Summarize now"
        ]
    )
    flow.run_guided(guided_config, ui=ui)
    assert "Artifacts" in ui.console().text
    assert str(report) in ui.console().text


def test_guided_stop_at_confirm_skips_summary(guided_config, tmp_path, monkeypatch):
    report = _mock_pipeline(monkeypatch, tmp_path)
    from minutia.prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds

    ui = FakeUI(
        selects=[
            0,
            list_prompt_kinds().index(DEFAULT_PROMPT_KIND),
            2,
            1,
        ]  # confirm → "Stop here"
    )
    flow.run_guided(guided_config, ui=ui)
    text = ui.console().text
    assert "Artifacts" in text
    assert str(report) not in text  # summary never generated


def test_guided_notes_paste_is_persisted(guided_config, tmp_path, monkeypatch):
    _mock_pipeline(monkeypatch, tmp_path)
    from minutia.prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds

    ui = FakeUI(
        selects=[
            0,
            list_prompt_kinds().index(DEFAULT_PROMPT_KIND),
            0,
            0,
        ],  # notes → "Paste notes"
        notes=["desktop=Alice, mic=Nick"],
    )
    flow.run_guided(guided_config, ui=ui)
    notes_file = tmp_path / "out" / "standup" / "notes.md"
    assert notes_file.exists()
    assert "desktop=Alice" in notes_file.read_text(encoding="utf-8")


def test_guided_stage_failure_is_reported_not_raised(
    guided_config, tmp_path, monkeypatch
):
    _mock_pipeline(monkeypatch, tmp_path)

    def boom(*a, **k):
        raise RuntimeError("ffmpeg boom")

    monkeypatch.setattr("minutia.steps.video_extraction.process_mkv_file", boom)
    from minutia.prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds

    # recording, style, notes="No notes" — fails during extract, before the cost confirm.
    ui = FakeUI(selects=[0, list_prompt_kinds().index(DEFAULT_PROMPT_KIND), 2])
    flow.run_guided(guided_config, ui=ui)  # must not raise
    text = ui.console().text
    assert "failed" in text.lower()
    assert "ffmpeg boom" in text


def test_guided_no_recordings_exits_early(tmp_path):
    empty = tmp_path / "recordings"
    empty.mkdir()
    config = MinutiaSettings(recordings_dir=empty, base_output_dir=tmp_path / "out")
    ui = FakeUI()
    flow.run_guided(config, ui=ui)
    assert "No .mkv files" in ui.console().text


def test_guided_without_recordings_dir_redirects_to_setup(tmp_path):
    config = MinutiaSettings(base_output_dir=tmp_path / "out")
    ui = FakeUI()
    flow.run_guided(config, ui=ui)
    assert "minutia setup" in ui.console().text
