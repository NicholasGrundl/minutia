"""Run the real minutia wizard against a fixture, with the slow steps faked.

Use it to try or show the wizard without a real meeting (the README screenshots
come from ``screenshots.py`` next to this file). The wizard itself is untouched: the same entry point, screens, keys and
progress view a user gets. Only the work behind the progress bar is replaced:

* audio extraction and transcription copy the ``microphone_only`` fixture outputs
  instead of running ffmpeg and Whisper;
* summarization returns the fixture summary instead of calling the Anthropic API.

So a run takes a few seconds, is the same every time, and needs no API key, GPU or
network. Merging and the token/cost estimate are the real code.

Usage (from the repo root)::

    uv run python scripts/demo/wizard_demo.py            # drive it by hand
    uv run python scripts/demo/wizard_demo.py --speed 0  # no artificial delays
    just demo                                            # the same, via just

Everything is written under ``/tmp/minutia-demo`` (recreated on each run), so no
personal path appears on screen.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import types
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "scenarios" / "microphone_only"
DEMO_ROOT = Path("/tmp/minutia-demo")
MARKER = DEMO_ROOT / ".minutia-demo"

# (file name, modified time) for the picker. All three are copies of the fixture
# recording; the first is the newest, so it is the row the cursor starts on.
RECORDINGS = (
    ("2026-11-10 14-02-11.mkv", datetime(2026, 11, 10, 14, 31)),
    ("2026-11-06 09-30-48.mkv", datetime(2026, 11, 6, 10, 4)),
    ("2026-11-03 16-15-02.mkv", datetime(2026, 11, 3, 16, 52)),
)
REPORT_NAME = "20261110_weekly_sync_summary.md"

_speed = 1.0


def _pause(seconds: float) -> None:
    time.sleep(seconds * _speed)


def _narrate(lines: tuple[tuple[float, str], ...]) -> None:
    """Log each line after its delay, so the wizard's live log tail has content."""
    from minutia.logging import logger

    for delay, line in lines:
        _pause(delay)
        logger.info(line)


def _build_demo_dir() -> tuple[Path, Path]:
    """Recreate the demo workspace; return ``(recordings_dir, output_dir)``."""
    if DEMO_ROOT.exists():
        if not MARKER.exists():
            sys.exit(f"{DEMO_ROOT} exists and was not created by this script.")
        shutil.rmtree(DEMO_ROOT)
    recordings = DEMO_ROOT / "recordings"
    output = DEMO_ROOT / "output"
    recordings.mkdir(parents=True)
    output.mkdir()
    MARKER.touch()
    for name, modified in RECORDINGS:
        target = recordings / name
        shutil.copyfile(FIXTURE / "input.mkv", target)
        stamp = modified.timestamp()
        os.utime(target, (stamp, stamp))
    return recordings, output


# --- Fakes for the slow steps --------------------------------------------------------


def fake_process_mkv_file(
    input_file: str,
    output_dir: str,
    mic_track_number: int = 3,
    desktop_track_number: int = 2,
) -> dict[str, str]:
    out = Path(output_dir)
    _narrate(
        (
            (0.3, f"Probing {Path(input_file).name}"),
            (0.5, f"Extracting track {mic_track_number} -> microphone_audio.wav"),
            (0.6, f"Extracting track {desktop_track_number} -> desktop_audio.wav"),
        )
    )
    files = {}
    for kind in ("microphone", "desktop"):
        target = out / f"{kind}_audio.wav"
        shutil.copyfile(FIXTURE / "01_extracted" / f"{kind}_audio.wav", target)
        files[kind] = str(target)
    _pause(0.4)
    return files


def fake_process_audio_files(
    mic_audio: str,
    desktop_audio: str,
    output_dir: str,
    whisper_model_name: str = "medium.en",
    use_gpu: bool = True,
) -> dict[str, str]:
    out = Path(output_dir)
    _narrate(
        (
            (0.3, f"Loading Whisper model {whisper_model_name} (cuda)"),
            (0.8, "Transcribing microphone_audio.wav"),
            (0.5, "microphone  25%"),
            (0.5, "microphone  50%"),
            (0.5, "microphone  75%"),
            (0.5, "microphone 100%"),
            (0.3, "Transcribing desktop_audio.wav"),
            (0.5, "desktop  50%"),
            (0.5, "desktop 100%"),
        )
    )
    files = {}
    for kind in ("microphone", "desktop"):
        source = (
            FIXTURE / "02_transcribed" / f"{kind}-whisper-medium.en_transcription.json"
        )
        target = out / f"{kind}-whisper-{whisper_model_name}_transcription.json"
        shutil.copyfile(source, target)
        files[kind] = str(target)
    _pause(0.3)
    return files


def fake_generate_long_summary(transcript_text: str, **_: object) -> str:
    _narrate(
        (
            (0.3, "Sending transcript to the model"),
            (1.0, "Receiving summary"),
            (1.2, "Summary complete"),
        )
    )
    (summary,) = (FIXTURE / "04_summarized").glob("*.md")
    return summary.read_text(encoding="utf-8")


def fake_create_markdown_report(
    content: str, output_path: str | Path, *_: object, **__: object
) -> Path:
    from minutia.logging import logger

    report = Path(output_path) / REPORT_NAME
    logger.info("Writing markdown report to {}", report)
    report.write_text(content, encoding="utf-8")
    _pause(0.4)
    return report


def _install_fakes() -> None:
    """Swap the slow step functions at their source modules (the wizard imports lazily).

    ``audio_transcription`` is replaced wholesale with a stub module so torch and
    Whisper are never imported: the demo starts as fast as ``minutia --help``.
    """
    import minutia.steps  # noqa: F401 - parent package must exist before the stub
    from minutia.steps import summarize_transcript, video_extraction

    stub = types.ModuleType("minutia.steps.audio_transcription")
    stub.process_audio_files = fake_process_audio_files  # type: ignore[attr-defined]
    sys.modules["minutia.steps.audio_transcription"] = stub

    video_extraction.process_mkv_file = fake_process_mkv_file
    summarize_transcript.generate_long_summary = fake_generate_long_summary
    summarize_transcript.create_markdown_report = fake_create_markdown_report


def main() -> None:
    global _speed
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="multiplier for the artificial delays (0 = none, 2 = twice as slow)",
    )
    _speed = parser.parse_args().speed

    recordings, output = _build_demo_dir()
    # Settings come from the process environment, which outranks the user config.
    # The key is a placeholder: nothing here talks to the API.
    os.environ.update(
        {
            "MINUTIA_RECORDINGS_DIR": str(recordings),
            "MINUTIA_OUTPUT_DIR": str(output),
            "MINUTIA_WHISPER_MODEL": "medium.en",
            "ANTHROPIC_API_KEY": "demo-key-not-used",
        }
    )
    os.environ.pop("MINUTIA_ANTHROPIC_API_KEY", None)
    _install_fakes()

    from minutia.cli import main as minutia_main

    sys.argv = ["minutia", "--no-env-file"]
    minutia_main()


if __name__ == "__main__":
    main()
