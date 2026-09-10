"""Presentation chrome for the minutia wizard — a hand-rolled rich full-screen renderer.

Everything visual about the wizard lives here so the look can be iterated in one place. Rather than
clear+redraw (which fights the terminal scroll region), every screen is painted by
:class:`rich.live.Live` on the **alternate screen**: a persistent header — the ``minutia`` wordmark
on the left, a live **waveform** + pipeline telemetry on the right (the waveform doubles as the
product's icon) — that never scrolls, then a rule, then the pane content.

The wizard *logic* (setup / guided-run flows) lives in :mod:`flow` (a later task); this module only
draws and reads keys. Key input is read with :mod:`yakh` (dist ``python-yakh``) — no web/ML weight,
so bare dispatch stays cold-start cheap.

Look is a set of **live-tweakable constants** at the top: the wine palette, the wordmark art, the
tagline, the waveform glyphs, and the selection cursor. Edit them here to reskin the whole wizard.

Testability: ``select`` / ``prompt_text`` / ``prompt_notes`` / ``run_staged_progress`` all accept an
injectable ``key_source`` (yields normalized tokens) and ``render`` (receives each frame), so tests
drive the flows without a real terminal.
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# --- Wine palette (live-tweakable) --------------------------------------------------------------
# WINE is the deep anchor / brand (#420f18). It is a *fill* color: near-invisible as small
# foreground text on a dark terminal, but strong as a highlight bar behind light text and as the
# rule / progress fill. ON_WINE is the light text drawn on a wine fill.
WINE = "#420f18"
ON_WINE = "#f4ecec"
FACE_STYLE = "bold #f2ecec"  # wordmark solid blocks (█ ▀ ▄)
FRAME_STYLE = "#7a6169"  # wordmark dim framing (░) — a wine-biased grey
DIM_STYLE = "#93787f"  # tagline, footers, secondary telemetry
ACCENT_STYLE = WINE  # rule, waveform, the active dot, progress fill
SELECT_STYLE = f"bold {ON_WINE} on {WINE}"  # selected menu row = a wine highlight bar
SELECT_CURSOR = "❯"
TAGLINE = "meeting notes, distilled"

# --- Wordmark (pagga figlet 'minutia'; the ░ frame + █▀▄ faces read as two tones) ---------------
WORDMARK = "\n".join(
    (
        "░█▄█░▀█▀░█▀█░█░█░▀█▀░▀█▀░█▀█",
        "░█░█░░█░░█░█░█░█░░█░░░█░░█▀█",
        "░▀░▀░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀░▀",
    )
)
_FACE_CHS = frozenset("█▀▄")
_FRAME_CHS = frozenset("░")

# --- Waveform (the icon + the activity indicator) -----------------------------------------------
_WAVE_GLYPHS = "▁▂▃▄▅▆▇█"
_WAVE_WIDTH = 10
_WAVE_SPEED = 6.0  # phase advance per second while active

# Width of the hand-drawn staged progress bar (characters).
_BAR_WIDTH = 30

# Footers (keystroke hints, shown on every screen).
SELECT_FOOTER = "↑/↓ move · Enter select · Esc cancel"
FIELD_FOOTER = "Enter confirm · Esc back"
NOTES_FOOTER = "Enter newline · Ctrl-D submit · Esc back"

# Normalized key tokens the interactive loops act on (decoupled from yakh so tests need no tty).
Token = str | tuple[str, str]

_console = Console()


def console() -> Console:
    """The shared wizard console (so the logic layer can print through the same stream)."""
    return _console


# --- Header / telemetry -------------------------------------------------------------------------


@dataclass
class HeaderStatus:
    """The live state the header's right-hand panel reflects.

    ``state`` is the pipeline stage label (``idle`` / ``extract`` / ``transcribe`` / ``merge`` /
    ``summarize`` / ``done``); ``active`` drives the waveform animation + the ``●`` dot; ``detail``
    is the elapsed-time line (or any short status); ``wave_phase`` scrolls the waveform.
    """

    language: str = "en"
    state: str = "idle"
    detail: str = ""
    active: bool = False
    wave_phase: float = 0.0


def waveform(phase: float, *, width: int = _WAVE_WIDTH, active: bool = True) -> Text:
    """A traveling audio-style waveform as rich :class:`Text` (the product icon + activity meter).

    ``active`` scrolls a two-harmonic wave across ``width`` glyphs; idle draws a near-flat line.
    Pure and deterministic in ``phase`` — unit-tested without a terminal.
    """
    glyphs = _WAVE_GLYPHS
    text = Text()
    for i in range(width):
        if active:
            a = (math.sin(i * 0.9 + phase) + 1) / 2
            b = (math.sin(i * 0.5 - phase * 1.3) + 1) / 2
            value = 0.55 * a + 0.45 * b
        else:
            value = 0.12
        index = max(0, min(len(glyphs) - 1, round(value * (len(glyphs) - 1))))
        text.append(glyphs[index], style=ACCENT_STYLE)
    return text


def format_elapsed(seconds: float) -> str:
    """Format an elapsed duration as ``MM:SS.s`` (the header's detail line)."""
    seconds = max(0.0, seconds)
    minutes, rem = divmod(seconds, 60)
    return f"{int(minutes):02d}:{rem:04.1f}"


def _wordmark_text() -> Text:
    """The wordmark as two-tone rich text: bold faces (█▀▄) over dim framing (░)."""
    text = Text()
    lines = WORDMARK.split("\n")
    for row, line in enumerate(lines):
        for char in line:
            if char in _FACE_CHS:
                text.append(char, style=FACE_STYLE)
            elif char in _FRAME_CHS:
                text.append(char, style=FRAME_STYLE)
            else:
                text.append(char)
        if row < len(lines) - 1:
            text.append("\n")
    return text


def _telemetry(status: HeaderStatus) -> Group:
    """The right-hand panel: waveform line, language + state line, detail (elapsed) line."""
    wave = waveform(status.wave_phase, active=status.active)

    state_line = Text(justify="right")
    state_line.append(f"{status.language.upper()} · ", style=DIM_STYLE)
    if status.active:
        state_line.append("● ", style=ACCENT_STYLE)
        state_line.append(status.state, style=FACE_STYLE)
    else:
        state_line.append("○ ", style=DIM_STYLE)
        state_line.append(status.state, style=DIM_STYLE)

    detail_line = Text(status.detail, style=DIM_STYLE, justify="right")
    wave.justify = "right"
    return Group(wave, state_line, detail_line)


def _header(status: HeaderStatus) -> Group:
    """Persistent header: wordmark + tagline (left), waveform + telemetry (right), then a rule."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    left = Group(_wordmark_text(), Text(TAGLINE, style=DIM_STYLE))
    grid.add_row(left, _telemetry(status))
    return Group(grid, Rule(style=WINE))


def _screen(panes: Sequence[RenderableType], status: HeaderStatus) -> Group:
    """Compose a full frame: persistent header + a blank line + the pane content."""
    return Group(_header(status), Text(), *panes)


# --- Key normalization --------------------------------------------------------------------------


def _default_key_source() -> Token:
    """Read one keystroke via yakh and normalize it to a :data:`Token`."""
    import yakh
    from yakh.key import Keys

    key = yakh.get_key()
    if key in (Keys.UP_ARROW, Keys.NUMPAD_UP_ARROW):
        return "up"
    if key in (Keys.DOWN_ARROW, Keys.NUMPAD_DOWN_ARROW):
        return "down"
    if key == Keys.ENTER:
        return "enter"
    if key == Keys.ESC:
        return "esc"
    if key == Keys.CTRL_C:
        return "ctrl_c"
    if key == Keys.CTRL_D:
        return "ctrl_d"
    if key == Keys.BACKSPACE:
        return "backspace"
    if key.is_printable:
        return ("char", key.key)
    return "other"


def _flush_input() -> None:
    """Discard tty input buffered *before* the current screen painted (cold-start Enter-mashing).

    Best-effort and silent: a flush failure (no tty, redirected stdin, tests) must never break the
    wizard.
    """
    try:
        import sys

        if not sys.stdin.isatty():
            return
        if sys.platform == "win32":
            import msvcrt

            while msvcrt.kbhit():
                msvcrt.getwch()
        else:
            import termios

            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass  # noqa: S110


def _run_interactive(
    frame_fn: Callable[[], Group],
    handle: Callable[[Token], tuple[str, Any] | None],
    *,
    key_source: Callable[[], Token] | None,
    render: Callable[[RenderableType], None] | None,
) -> Any:
    """Drive one interactive screen. ``handle`` returns ``("return", value)`` to stop.

    Headless path (``render`` given): paint via ``render`` and read tokens from ``key_source`` — no
    tty. Live path: paint via :class:`rich.live.Live` on the alternate screen and read via
    :func:`_default_key_source`.
    """
    if render is not None:
        get_key = key_source or _default_key_source
        render(frame_fn())
        while True:
            result = handle(get_key())
            if result is not None:
                return result[1]
            render(frame_fn())

    get_key = key_source or _default_key_source
    with Live(frame_fn(), screen=True, auto_refresh=False, console=_console) as live:
        _flush_input()
        while True:
            result = handle(get_key())
            if result is not None:
                return result[1]
            live.update(frame_fn(), refresh=True)


# --- Interactive primitives ---------------------------------------------------------------------


def select(
    panes: Sequence[RenderableType],
    options: Sequence[str],
    *,
    cursor_index: int = 0,
    footer: str = SELECT_FOOTER,
    status: HeaderStatus | None = None,
    key_source: Callable[[], Token] | None = None,
    render: Callable[[RenderableType], None] | None = None,
) -> int | None:
    """Full-screen single-select. The highlighted row is a wine bar. Returns the chosen index.

    Returns the index on Enter, or ``None`` on Esc / Ctrl-C.
    """
    status = status or HeaderStatus()
    width = max((len(opt) for opt in options), default=0)
    state = {"idx": cursor_index}

    def frame_fn() -> Group:
        rows: list[RenderableType] = []
        for i, opt in enumerate(options):
            if i == state["idx"]:
                rows.append(Text(f"{SELECT_CURSOR} {opt:<{width}}  ", style=SELECT_STYLE))
            else:
                rows.append(Text(f"  {opt}"))
        rows += [Text(), Text(footer, style=DIM_STYLE)]
        return _screen([*panes, *rows], status)

    def handle(token: Token) -> tuple[str, Any] | None:
        name = token[0] if isinstance(token, tuple) else token
        if name == "up":
            state["idx"] = (state["idx"] - 1) % len(options)
        elif name == "down":
            state["idx"] = (state["idx"] + 1) % len(options)
        elif name == "enter":
            return ("return", state["idx"])
        elif name in ("esc", "ctrl_c"):
            return ("return", None)
        return None

    return _run_interactive(frame_fn, handle, key_source=key_source, render=render)


def prompt_text(
    panes: Sequence[RenderableType],
    *,
    title: str = "Type or paste, then Enter",
    footer: str = FIELD_FOOTER,
    error: str | None = None,
    status: HeaderStatus | None = None,
    key_source: Callable[[], Token] | None = None,
    render: Callable[[RenderableType], None] | None = None,
) -> str | None:
    """Full-screen single-line field (paste-friendly). Returns the raw text, or ``None`` on Esc."""
    status = status or HeaderStatus()
    state = {"buffer": ""}

    def frame_fn() -> Group:
        line = Text("> ")
        line.append(state["buffer"])
        line.append("▏", style=WINE)
        panes_out: list[RenderableType] = [*panes, Text(title, style="bold")]
        if error is not None:
            panes_out.append(Text(error, style="bold red"))
        panes_out += [line, Text(), Text(footer, style=DIM_STYLE)]
        return _screen(panes_out, status)

    def handle(token: Token) -> tuple[str, Any] | None:
        name = token[0] if isinstance(token, tuple) else token
        if name == "enter":
            return ("return", state["buffer"])
        if name in ("esc", "ctrl_c"):
            return ("return", None)
        if name == "backspace":
            state["buffer"] = state["buffer"][:-1]
        elif name == "char":
            state["buffer"] += token[1]
        return None

    return _run_interactive(frame_fn, handle, key_source=key_source, render=render)


def prompt_notes(
    panes: Sequence[RenderableType],
    *,
    title: str = "Notes — paste freely",
    footer: str = NOTES_FOOTER,
    status: HeaderStatus | None = None,
    key_source: Callable[[], Token] | None = None,
    render: Callable[[RenderableType], None] | None = None,
) -> str | None:
    """Full-screen **multi-line** field: Enter inserts a newline, Ctrl-D submits, Esc cancels.

    Handles multi-line paste (each pasted newline arrives as an Enter token). Returns the full text
    (may be empty — caller decides what empty means), or ``None`` on Esc / Ctrl-C.
    """
    status = status or HeaderStatus()
    state = {"buffer": ""}

    def frame_fn() -> Group:
        body = Text(state["buffer"])
        body.append("▏", style=WINE)
        panes_out: list[RenderableType] = [
            *panes,
            Text(title, style="bold"),
            Text(),
            body,
            Text(),
            Text(footer, style=DIM_STYLE),
        ]
        return _screen(panes_out, status)

    def handle(token: Token) -> tuple[str, Any] | None:
        name = token[0] if isinstance(token, tuple) else token
        if name == "ctrl_d":
            return ("return", state["buffer"])
        if name in ("esc", "ctrl_c"):
            return ("return", None)
        if name == "enter":
            state["buffer"] += "\n"
        elif name == "backspace":
            state["buffer"] = state["buffer"][:-1]
        elif name == "char":
            state["buffer"] += token[1]
        return None

    return _run_interactive(frame_fn, handle, key_source=key_source, render=render)


# --- Staged progress (drives the header telemetry: stage + waveform + elapsed) -------------------


@dataclass(frozen=True)
class Step:
    """One unit of the staged pipeline: the bar sits at ``fraction`` while ``run`` blocks.

    ``fraction`` is cosmetic + monotonic (where the bar dwells during this step); ``label`` is the
    line above the bar; ``state`` is the short header telemetry label (defaults to ``label``);
    ``run`` is the blocking work whose return value is collected in order.
    """

    fraction: float
    label: str
    run: Callable[[], Any]
    state: str = ""


def _progress_frame(
    panes: Sequence[RenderableType], fraction: float, label: str, status: HeaderStatus
) -> Group:
    """Compose the progress pane: header (telemetry) + label line + hand-drawn wine bar."""
    filled = round(fraction * _BAR_WIDTH)
    bar = Text()
    bar.append("█" * filled, style=WINE)
    bar.append("░" * (_BAR_WIDTH - filled), style=FRAME_STYLE)
    bar.append(f"  {int(fraction * 100):>3d}%", style=DIM_STYLE)
    return _screen([*panes, Text(label), bar], status)


def _run_steps(
    steps: Sequence[Step],
    setup_index: int,
    status: HeaderStatus,
    paint: Callable[[float, str], None],
) -> list[Any]:
    """The dumb loop shared by the live + injected paths (see :func:`run_staged_progress`)."""
    results: list[Any] = []
    for index, step in enumerate(steps):
        status.state = step.state or step.label
        status.active = True
        paint(step.fraction, step.label)  # render-before-block
        try:
            results.append(step.run())
        except Exception:
            if index == setup_index:
                raise  # setup failure is real
            results.append(None)  # warmup failure is best-effort
    status.state = "done"
    status.active = False
    paint(1.0, "Ready")
    return results


def run_staged_progress(
    steps: Sequence[Step],
    panes: Sequence[RenderableType],
    *,
    status: HeaderStatus | None = None,
    setup_index: int = 0,
    render: Callable[[float, str], None] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> list[Any]:
    """Run ``steps`` under the progress bar; return results aligned to steps.

    Live path: a daemon animator repaints ~12x/s so the header **waveform scrolls** and the
    **elapsed** clock ticks while each (blocking) ``step.run`` executes; the bar jumps to each
    step's ``fraction`` at its boundary and lands on ``1.0`` when the last step returns.

    ``render`` is injectable: pass a recorder ``(fraction, label) -> None`` in tests to assert
    ordering without a terminal (no thread, no tty).
    """
    status = status or HeaderStatus()

    if render is not None:
        return _run_steps(steps, setup_index, status, render)

    start = clock()
    lock = threading.Lock()
    stop = threading.Event()
    cur_fraction = 0.0
    cur_label = ""

    with Live(
        _progress_frame(panes, 0.0, "", status),
        screen=True,
        auto_refresh=False,
        console=_console,
    ) as live:

        def repaint() -> None:
            status.wave_phase = (clock() - start) * _WAVE_SPEED
            status.detail = format_elapsed(clock() - start)
            with lock:
                live.update(
                    _progress_frame(panes, cur_fraction, cur_label, status),
                    refresh=True,
                )

        def animator() -> None:
            while not stop.wait(1 / 12):
                repaint()

        thread = threading.Thread(target=animator, daemon=True)
        thread.start()

        def paint(fraction: float, label: str) -> None:
            nonlocal cur_fraction, cur_label
            cur_fraction = fraction
            cur_label = label
            repaint()

        try:
            return _run_steps(steps, setup_index, status, paint)
        finally:
            stop.set()
            thread.join(timeout=0.5)
