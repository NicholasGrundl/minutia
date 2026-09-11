"""Unit tests for the wizard presentation layer (headless).

The interactive primitives take an injected ``key_source`` (yields normalized tokens) and
``render`` (receives each frame), so we drive full flows without a real terminal. The pure helpers
(waveform, elapsed formatting, header composition) are asserted directly.
"""

from __future__ import annotations

import subprocess
import sys

from minutia.cli.wizard import tui


def _keys(*tokens):
    """A key_source callable that yields the given tokens in order."""
    queue = list(tokens)
    return lambda: queue.pop(0)


class TestPureHelpers:
    def test_waveform_width_and_glyphs(self):
        text = tui.waveform(0.0, width=8, active=True)
        assert len(text.plain) == 8
        assert set(text.plain) <= set(tui._WAVE_GLYPHS)

    def test_waveform_idle_is_near_flat(self):
        text = tui.waveform(3.3, width=12, active=False)
        # Idle draws a single low glyph across the whole width.
        assert set(text.plain) == {tui._WAVE_GLYPHS[1]}

    def test_waveform_is_deterministic_in_phase(self):
        assert tui.waveform(1.5, width=10).plain == tui.waveform(1.5, width=10).plain

    def test_format_elapsed(self):
        assert tui.format_elapsed(0) == "00:00.0"
        assert tui.format_elapsed(65.4) == "01:05.4"
        assert tui.format_elapsed(-1) == "00:00.0"

    def test_header_renders_without_error(self):
        # Renders the full frame (wordmark + telemetry + rule) to plain text via the console.
        frame = tui._screen(
            [], tui.HeaderStatus(state="transcribe", active=True, detail="00:12.3")
        )
        with tui.console().capture() as cap:
            tui.console().print(frame)
        out = cap.get()
        assert "minutia" not in out  # wordmark is block art, not literal text
        assert "TRANSCRIBE".lower() in out.lower()
        assert "00:12.3" in out


class TestSelect:
    def test_arrow_then_enter_returns_index(self):
        frames: list = []
        result = tui.select(
            [],
            ["Guided run", "Setup", "Info"],
            key_source=_keys("down", "down", "enter"),
            render=frames.append,
        )
        assert result == 2
        assert frames  # painted at least the initial frame

    def test_wraps_upward(self):
        result = tui.select(
            [], ["a", "b", "c"], key_source=_keys("up", "enter"), render=lambda _f: None
        )
        assert result == 2  # up from index 0 wraps to last

    def test_esc_cancels(self):
        result = tui.select(
            [], ["a", "b"], key_source=_keys("esc"), render=lambda _f: None
        )
        assert result is None


class TestPromptText:
    def test_types_and_confirms(self):
        result = tui.prompt_text(
            [],
            key_source=_keys(("char", "h"), ("char", "i"), "enter"),
            render=lambda _f: None,
        )
        assert result == "hi"

    def test_backspace_edits(self):
        result = tui.prompt_text(
            [],
            key_source=_keys(("char", "a"), ("char", "b"), "backspace", "enter"),
            render=lambda _f: None,
        )
        assert result == "a"

    def test_esc_returns_none(self):
        result = tui.prompt_text([], key_source=_keys("esc"), render=lambda _f: None)
        assert result is None


class TestPromptNotes:
    def test_enter_inserts_newline_ctrl_d_submits(self):
        result = tui.prompt_notes(
            [],
            key_source=_keys(
                ("char", "a"), "enter", ("char", "b"), ("char", "c"), "ctrl_d"
            ),
            render=lambda _f: None,
        )
        assert result == "a\nbc"

    def test_esc_cancels(self):
        result = tui.prompt_notes(
            [], key_source=_keys(("char", "x"), "esc"), render=lambda _f: None
        )
        assert result is None


class TestStagedProgress:
    def test_runs_steps_in_order_and_returns_results(self):
        painted: list[tuple[float, str]] = []
        steps = [
            tui.Step(0.3, "extract", lambda: "A"),
            tui.Step(0.7, "transcribe", lambda: "B"),
        ]
        results = tui.run_staged_progress(
            steps, [], render=lambda fraction, label: painted.append((fraction, label))
        )
        assert results == ["A", "B"]
        assert painted == [(0.3, "extract"), (0.7, "transcribe"), (1.0, "Ready")]

    def test_step_failure_returns_step_error(self):
        steps = [
            tui.Step(
                0.3, "extract", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
            )
        ]
        results = tui.run_staged_progress(steps, [], render=lambda *_: None)
        assert len(results) == 1
        assert isinstance(results[0], tui.StepError)
        assert results[0].label == "extract"
        assert "boom" in results[0].message

    def test_failure_stops_remaining_steps(self):
        def boom():
            raise RuntimeError("kaboom")

        steps = [
            tui.Step(0.3, "a", lambda: "ok"),
            tui.Step(0.6, "b", boom),
            tui.Step(0.9, "c", lambda: "never"),
        ]
        results = tui.run_staged_progress(steps, [], render=lambda *_: None)
        assert results[0] == "ok"
        assert isinstance(results[1], tui.StepError)
        assert len(results) == 2  # step c never runs


def test_importing_tui_does_not_import_yakh_or_heavy_deps():
    """yakh is imported lazily (only when reading keys), and no ML stack is pulled."""
    probe = (
        "import sys; import minutia.cli.wizard.tui; "
        "print(','.join(m for m in ('yakh','torch','whisper','anthropic') if m in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "", f"unexpected imports: {result.stdout!r}"
