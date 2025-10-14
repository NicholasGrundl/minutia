"""
Path management utilities for Minutia pipeline runs.

The :class:`RunPaths` dataclass provides a canonical view over all filesystem
locations used during a processing run. It encapsulates directory creation,
collision handling, and cleanup behaviour so that pipeline stages can focus on
their core responsibilities.
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class CleanupPolicy(Enum):
    """Policies for removing intermediate run artifacts."""

    KEEP_ALL = "keep_all"
    KEEP_FINAL = "keep_final"
    CLEANUP_ON_ERROR = "cleanup_on_error"


def _slugify(value: str) -> str:
    """Return a filesystem-safe slug derived from the input value."""
    value = value.lower()
    value = re.sub(r"[^\w\-]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-") or "run"


def _current_iso_date() -> str:
    """Return current date in ISO format (YYYY-MM-DD)."""
    return datetime.datetime.now(tz=datetime.timezone.utc).date().isoformat()


def resolve_run_directory(base_name: str, base_dir: Path, max_attempts: int = 100) -> Path:
    """
    Resolve a unique run directory under ``base_dir`` using collision handling.

    Strategy:
        - First attempt: {base_name}
        - Collisions: {base_name}_2, {base_name}_3, etc.
        - After ``max_attempts`` attempts, raise ``RuntimeError``.
    """
    if max_attempts < 1:
        raise RuntimeError("max_attempts must be >= 1 to resolve a run directory.")

    candidate = base_dir / base_name
    if not candidate.exists():
        return candidate

    for suffix in range(2, max_attempts + 1):
        alt = base_dir / f"{base_name}_{suffix}"
        if not alt.exists():
            return alt
    raise RuntimeError(
        f"Unable to resolve unique run directory for '{base_name}' after {max_attempts} attempts."
    )


@dataclass(frozen=True)
class RunPaths:
    """
    Canonical filesystem locations for a single pipeline run.

    Instances are constructed via :meth:`from_video_input` or
    :meth:`from_audio_inputs` to ensure consistent naming conventions.
    """

    run_root: Path
    input_path: Path
    audio_dir: Path
    transcripts_dir: Path
    microphone_audio: Path
    desktop_audio: Path
    merged_transcript: Path
    summary_file: Path
    metadata_file: Path
    logs_file: Path

    @classmethod
    def from_video_input(
        cls,
        input_path: Union[str, Path],
        base_output_dir: Optional[Path] = None,
        run_suffix: Optional[str] = None,
    ) -> "RunPaths":
        """Create :class:`RunPaths` from an OBS recording."""
        input_path = Path(input_path).expanduser().resolve()
        if not input_path.exists() or not input_path.is_file():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        base_output_dir = (base_output_dir or Path("./runs")).expanduser().resolve()
        base_output_dir.mkdir(parents=True, exist_ok=True)

        date_prefix = _current_iso_date()
        slug = _slugify(input_path.stem)
        run_dir_name = f"{date_prefix}_{slug}"
        if run_suffix:
            run_dir_name = f"{run_dir_name}_{_slugify(run_suffix)}"

        run_root = resolve_run_directory(run_dir_name, base_output_dir)

        return cls._build(run_root=run_root, input_path=input_path)

    @classmethod
    def from_audio_inputs(
        cls,
        mic_audio_path: Union[str, Path],
        desktop_audio_path: Union[str, Path],
        base_output_dir: Optional[Path] = None,
    ) -> "RunPaths":
        """Create :class:`RunPaths` when starting from pre-extracted audio files."""
        mic_audio_path = Path(mic_audio_path).expanduser().resolve()
        desktop_audio_path = Path(desktop_audio_path).expanduser().resolve()

        for path in (mic_audio_path, desktop_audio_path):
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"Audio input not found: {path}")

        base_output_dir = (base_output_dir or Path("./runs")).expanduser().resolve()
        base_output_dir.mkdir(parents=True, exist_ok=True)

        parent_name = mic_audio_path.parent.name or mic_audio_path.stem
        date_prefix = _current_iso_date()
        run_dir_name = f"{date_prefix}_{_slugify(parent_name)}"
        run_root = resolve_run_directory(run_dir_name, base_output_dir)

        return cls._build(run_root=run_root, input_path=mic_audio_path)

    @classmethod
    def _build(cls, run_root: Path, input_path: Path) -> "RunPaths":
        audio_dir = run_root / "audio"
        transcripts_dir = run_root / "transcripts"
        microphone_audio = audio_dir / "microphone_audio.wav"
        desktop_audio = audio_dir / "desktop_audio.wav"
        merged_transcript = run_root / "merged_transcript.json"
        summary_file = run_root / "summary.txt"
        metadata_file = run_root / "metadata.json"
        logs_file = run_root / "minutia.log"

        return cls(
            run_root=run_root,
            input_path=input_path,
            audio_dir=audio_dir,
            transcripts_dir=transcripts_dir,
            microphone_audio=microphone_audio,
            desktop_audio=desktop_audio,
            merged_transcript=merged_transcript,
            summary_file=summary_file,
            metadata_file=metadata_file,
            logs_file=logs_file,
        )

    def ensure_directories(self) -> None:
        """Create required directories with 0755 permissions."""
        for directory in {self.run_root, self.audio_dir, self.transcripts_dir}:
            directory.mkdir(parents=True, exist_ok=True)
            os.chmod(directory, 0o755)

    def cleanup(self, policy: CleanupPolicy = CleanupPolicy.KEEP_ALL) -> None:
        """Clean up intermediate files based on the provided policy."""
        if policy == CleanupPolicy.KEEP_ALL:
            return

        if policy == CleanupPolicy.KEEP_FINAL:
            for path in (self.microphone_audio, self.desktop_audio):
                if path.exists():
                    path.unlink()
            if self.audio_dir.exists() and not any(self.audio_dir.iterdir()):
                self.audio_dir.rmdir()
            return

        if policy == CleanupPolicy.CLEANUP_ON_ERROR:
            if self.run_root.exists():
                shutil.rmtree(self.run_root)
            return

        raise ValueError(f"Unknown cleanup policy: {policy}")
