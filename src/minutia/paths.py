"""
Path management utilities for Minutia pipeline runs.

This module provides the :class:`RunPaths` dataclass, a centralized and
immutable structure for managing all filesystem locations for a single data
processing run. It standardizes directory creation, naming conventions, and
collision handling, allowing pipeline steps to operate on a canonical set of
paths.

The main entry points are the factory methods :meth:`RunPaths.from_video_input`
and :meth:`RunPaths.from_audio_inputs`, which construct the path hierarchy
based on the initial input files.
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CleanupPolicy(Enum):
    """
    Defines policies for cleaning up intermediate run artifacts.

    Attributes
    ----------
    KEEP_ALL
        Retain all files generated during the run, including intermediate audio
        and transcript files.
    KEEP_FINAL
        Remove intermediate files (e.g., extracted audio tracks) but keep the
        final outputs like the merged transcript and summary.
    CLEANUP_ON_ERROR
        Remove the entire run directory and all its contents if an error occurs
        during the pipeline execution.
    """

    KEEP_ALL = "keep_all"
    KEEP_FINAL = "keep_final"
    CLEANUP_ON_ERROR = "cleanup_on_error"


def _slugify(value: str) -> str:
    """
    Convert a string into a filesystem-safe "slug".

    The slug is lowercased, with non-alphanumeric characters replaced by
    hyphens. Multiple consecutive hyphens are collapsed.

    Parameters
    ----------
    value : str
        The input string to convert.

    Returns
    -------
    str
        A filesystem-safe slug.

    Examples
    --------
    >>> _slugify("My Awesome Recording!! (2023)")
    'my-awesome-recording-2023'
    """
    value = value.lower()
    value = re.sub(r"[^\w\-]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-") or "run"


def _current_iso_date() -> str:
    """Return current date in ISO format (YYYY-MM-DD) in UTC."""
    return datetime.datetime.now(tz=datetime.timezone.utc).date().isoformat()


def resolve_run_directory(base_name: str, base_dir: Path, max_attempts: int = 100) -> Path:
    """
    Resolve a unique run directory under ``base_dir`` using collision handling.

    This function attempts to create a directory with `base_name`. If a
    directory with that name already exists, it appends an integer suffix
    (e.g., `_2`, `_3`) until a unique name is found.

    Parameters
    ----------
    base_name : str
        The desired initial name for the run directory.
    base_dir : Path
        The parent directory where the new run directory will be created.
    max_attempts : int, default=100
        The maximum number of suffixes to try before raising an error.

    Returns
    -------
    Path
        The path to the resolved unique run directory.

    Raises
    ------
    RuntimeError
        If a unique directory name cannot be found within `max_attempts`.
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

    This dataclass provides a structured, immutable view of all paths required
    for a pipeline run. It centralizes naming conventions and directory
    structure, ensuring that all pipeline components access files in a
    consistent manner.

    Instances should be created using the provided class methods
    :meth:`from_video_input` or :meth:`from_audio_inputs`.

    Attributes
    ----------
    run_root : Path
        The root directory for all files related to this run.
    input_path : Path
        The primary input file for the run (e.g., video or microphone audio).
    audio_dir : Path
        Directory to store intermediate audio files.
    transcripts_dir : Path
        Directory to store individual audio track transcripts.
    microphone_audio : Path
        Path to the extracted microphone audio file (.wav).
    desktop_audio : Path
        Path to the extracted desktop audio file (.wav).
    merged_transcript : Path
        Path to the final merged transcript file (.json).
    summary_file : Path
        Path to the final summary file (.txt).
    metadata_file : Path
        Path to the run metadata file (.json).
    logs_file : Path
        Path to the log file for the run.

    Examples
    --------
    >>> from pathlib import Path
    >>> # Create a dummy video file
    >>> video_file = Path("2023-10-26_my-meeting.mkv")
    >>> video_file.touch()
    >>>
    >>> paths = RunPaths.from_video_input(video_file, base_output_dir=Path("/tmp/runs"))
    >>> print(paths.run_root)
    /tmp/runs/2023-10-26_2023-10-26-my-meeting
    >>> print(paths.summary_file)
    /tmp/runs/2023-10-26_2023-10-26-my-meeting/summary.txt
    >>>
    >>> # Clean up the dummy file
    >>> video_file.unlink()
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
        input_path: str | Path,
        base_output_dir: Path | None = None,
        run_suffix: str | None = None,
    ) -> RunPaths:
        """
        Create :class:`RunPaths` from a source video file (e.g., an OBS recording).

        The run directory name is generated from the current date and a slug of
        the input video's filename.

        Parameters
        ----------
        input_path : str or Path
            Path to the source video file.
        base_output_dir : Path, optional
            The parent directory for all run outputs. Defaults to `./runs`.
        run_suffix : str, optional
            An optional suffix to append to the run directory name for
            additional context.

        Returns
        -------
        RunPaths
            An initialized `RunPaths` instance.

        Raises
        ------
        FileNotFoundError
            If the `input_path` does not exist or is not a file.
        """
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
        mic_audio_path: str | Path,
        desktop_audio_path: str | Path,
        base_output_dir: Path | None = None,
    ) -> RunPaths:
        """
        Create :class:`RunPaths` from pre-extracted audio files.

        The run directory name is generated from the current date and the parent
        directory name of the microphone audio file.

        Parameters
        ----------
        mic_audio_path : str or Path
            Path to the microphone audio file.
        desktop_audio_path : str or Path
            Path to the desktop audio file.
        base_output_dir : Path, optional
            The parent directory for all run outputs. Defaults to `./runs`.

        Returns
        -------
        RunPaths
            An initialized `RunPaths` instance.

        Raises
        ------
        FileNotFoundError
            If either audio input path does not exist or is not a file.
        """
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
    def _build(cls, run_root: Path, input_path: Path) -> RunPaths:
        """Construct the full set of paths from the run root."""
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
        """
        Create all necessary directories for the run.

        Ensures that `run_root`, `audio_dir`, and `transcripts_dir` exist,
        creating them if necessary with 0755 permissions.
        """
        for directory in {self.run_root, self.audio_dir, self.transcripts_dir}:
            directory.mkdir(parents=True, exist_ok=True)
            os.chmod(directory, 0o755)

    def cleanup(self, policy: CleanupPolicy = CleanupPolicy.KEEP_ALL) -> None:
        """
        Clean up intermediate or all files based on the provided policy.

        Parameters
        ----------
        policy : CleanupPolicy, default=CleanupPolicy.KEEP_ALL
            The cleanup policy to apply. See :class:`CleanupPolicy` for details.

        Raises
        ------
        ValueError
            If an unknown cleanup policy is provided.
        """
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
            self._safe_cleanup_on_error()
            return

        raise ValueError(f"Unknown cleanup policy: {policy}")
