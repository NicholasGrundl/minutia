"""Utilities for extracting audio tracks from OBS MKV recordings."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

import ffmpeg

from ..logging import logger


def get_video_info(file_path: Path) -> dict[str, Iterable[dict]]:
    """Return ffmpeg stream metadata for the provided MKV file."""
    probe = ffmpeg.probe(str(file_path))
    video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    return {"video": video_info, "audio_streams": audio_streams}


def extract_audio_track(input_file: Path, output_file: Path, track_index: int) -> None:
    """Extract a specific audio stream into a WAV file."""
    input_stream = ffmpeg.input(str(input_file))
    audio = input_stream[f"a:{track_index}"]
    output = ffmpeg.output(audio, str(output_file))
    ffmpeg.run(output, capture_stdout=False, capture_stderr=True)


def extract_all_audio_tracks(
    input_file: Path, output_directory: Path
) -> Iterable[Path]:
    """Extract every audio stream to numbered WAV files."""
    output_directory.mkdir(parents=True, exist_ok=True)
    audio_streams = get_video_info(input_file)["audio_streams"]
    extracted_files = []
    for index in range(len(audio_streams)):
        output_file = output_directory / f"audio_track_{index + 1}.wav"
        extract_audio_track(input_file, output_file, index)
        extracted_files.append(output_file)
    return extracted_files


def identify_audio_tracks(
    audio_files: Iterable[Path],
    mic_track_number: int = 3,
    desktop_track_number: int = 2,
) -> dict[str, Path]:
    """
    Identify microphone and desktop audio files based on track numbers.

    OBS numbers tracks starting at 1, so the generated filenames use the same
    convention (audio_track_1.wav, audio_track_2.wav, ...).
    """
    logger.info(
        "Identifying audio tracks (mic={}, desktop={})",
        mic_track_number,
        desktop_track_number,
    )
    track_lookup = {}
    for file in audio_files:
        suffix = file.stem.split("_")[-1]
        if suffix.isdigit():
            track_lookup[int(suffix)] = file

    microphone = track_lookup.get(mic_track_number)
    desktop = track_lookup.get(desktop_track_number)

    if microphone is None or desktop is None:
        logger.error("Available tracks: {}", sorted(track_lookup))
        raise ValueError("Could not identify both microphone and desktop audio files.")

    return {"microphone": microphone, "desktop": desktop}


def copy_and_rename_audio_files(
    identified_tracks: dict[str, Path], output_directory: Path
) -> dict[str, Path]:
    """Copy identified audio files with stable filenames for downstream steps."""
    output_directory.mkdir(parents=True, exist_ok=True)
    renamed_tracks = {}
    for track_type, file_path in identified_tracks.items():
        destination = output_directory / f"{track_type}_audio.wav"
        shutil.copy2(file_path, destination)
        renamed_tracks[track_type] = destination
    return renamed_tracks


def process_mkv_file(
    input_mkv: str,
    output_dir: str,
    *,
    mic_track_number: int = 3,
    desktop_track_number: int = 2,
) -> dict[str, str]:
    """Extract audio tracks from an MKV file and return microphone/desktop paths."""
    input_path = Path(input_mkv)
    output_path = Path(output_dir)

    logger.info("Processing MKV file {}", input_path)
    extracted_files = list(extract_all_audio_tracks(input_path, output_path))
    logger.info("Extracted {} audio tracks", len(extracted_files))

    identified_tracks = identify_audio_tracks(
        extracted_files,
        mic_track_number=mic_track_number,
        desktop_track_number=desktop_track_number,
    )
    renamed_tracks = copy_and_rename_audio_files(identified_tracks, output_path)

    logger.info("Microphone audio: {}", renamed_tracks["microphone"])
    logger.info("Desktop audio: {}", renamed_tracks["desktop"])

    return {key: str(path) for key, path in renamed_tracks.items()}
