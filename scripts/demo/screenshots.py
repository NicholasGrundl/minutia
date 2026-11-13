"""Render README screenshots of the wizard as SVG, in pure Python.

The wizard is drawn with rich, and rich can export what it draws as an SVG. This
script builds the same frames the wizard paints (through the TUI's own functions,
so the pictures follow the code) and writes them to ``docs/assets/``. No terminal,
recording tool, API key or network is involved.

Usage (from the repo root)::

    just screenshots        # or: uv run python scripts/demo/screenshots.py

To add a screenshot, write another ``_<name>_frame()`` function and list it in
``SHOTS``.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, RenderableType
from rich.terminal_theme import TerminalTheme
from rich.text import Text

from minutia.cli.wizard import tui
from minutia.prompts import DEFAULT_PROMPT_KIND, list_prompt_kinds

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs" / "assets"
WIDTH = 92

RECORDING = "2026-11-10 14-02-11.mkv"
PICKER_ROWS = (
    f"{RECORDING:<30}  2026-11-10 14:31   412.6 MB    47:12",
    f"{'2026-11-06 09-30-48.mkv':<30}  2026-11-06 10:04   268.3 MB    31:05",
    f"{'2026-11-03 16-15-02.mkv':<30}  2026-11-03 16:52   530.9 MB    58:40",
)

# A dark terminal that suits the wizard's wine palette.
THEME = TerminalTheme(
    (22, 18, 20),
    (232, 224, 225),
    [
        (22, 18, 20),
        (194, 86, 106),
        (143, 174, 139),
        (210, 180, 140),
        (138, 156, 194),
        (181, 138, 165),
        (138, 181, 176),
        (232, 224, 225),
    ],
    [
        (147, 120, 127),
        (217, 122, 139),
        (169, 199, 165),
        (227, 203, 167),
        (167, 182, 214),
        (203, 166, 190),
        (166, 205, 200),
        (255, 255, 255),
    ],
)


def _select_frame(title: str, options: list[str], cursor: int = 0) -> RenderableType:
    """The frame ``tui.select`` paints first, captured through its ``render`` hook."""
    frames: list[RenderableType] = []
    tui.select(
        [Text(title, style="bold")],
        options,
        cursor_index=cursor,
        render=frames.append,
        key_source=lambda: "enter",
    )
    return frames[0]


def _pick_frame() -> RenderableType:
    return _select_frame(
        "Pick a recording  (name · modified · size · length)", list(PICKER_ROWS)
    )


def _style_frame() -> RenderableType:
    kinds = list_prompt_kinds()
    return _select_frame("Summary style", kinds, kinds.index(DEFAULT_PROMPT_KIND))


def _progress_frame() -> RenderableType:
    status = tui.HeaderStatus(
        state="transcribe", active=True, detail="03:41.2", wave_phase=2.4
    )
    log_lines = [
        "14:32:07 INFO    Extracting track 3 -> microphone_audio.wav",
        "14:32:15 INFO    Extracting track 2 -> desktop_audio.wav",
        "14:32:24 INFO    Loading Whisper model medium.en (cuda)",
        "14:32:31 INFO    Transcribing microphone_audio.wav",
        "14:33:48 INFO    microphone  50%",
        "14:35:02 INFO    microphone 100%",
        "14:35:03 INFO    Transcribing desktop_audio.wav",
        "14:35:44 INFO    desktop  50%",
    ]
    return tui._progress_frame(
        [Text(f"Recording: {RECORDING}")], 0.6, "transcribing", status, log_lines
    )


SHOTS = {
    "wizard-pick": _pick_frame,
    "wizard-style": _style_frame,
    "wizard-progress": _progress_frame,
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build in SHOTS.items():
        console = Console(
            record=True, width=WIDTH, force_terminal=True, color_system="truecolor"
        )
        with open("/dev/null", "w") as sink:
            console.file = sink
            console.print(build())
        target = OUT_DIR / f"{name}.svg"
        console.save_svg(str(target), title="minutia", theme=THEME, unique_id=name)
        print(f"{target.relative_to(REPO_ROOT)}  {target.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
