import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..logging import logger

SCHEMA_VERSION = "1.0"

LEGACY_SEGMENT_PATTERN = re.compile(r"\[(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\]\s*(.+)")


def _normalise_segment(segment: Mapping[str, Any]) -> dict[str, Any]:
    """Ensure segment dictionaries expose start/end values with consistent keys."""
    start = segment.get("start_time", segment.get("start"))
    end = segment.get("end_time", segment.get("end"))
    if start is None or end is None:
        raise ValueError("segment is missing timing information")

    text = segment.get("text", "")
    normalised: dict[str, Any] = {
        "start_time": float(start),
        "end_time": float(end),
        "text": text.strip(),
    }

    optional_fields = (
        "id",
        "seek",
        "speaker",
        "tokens",
        "temperature",
        "avg_logprob",
        "compression_ratio",
        "no_speech_prob",
    )
    for field in optional_fields:
        value = segment.get(field)
        if value is not None:
            normalised[field] = value
    return normalised


def _parse_legacy_transcript(path: Path) -> dict[str, Any]:
    """Parse transcripts emitted by earlier plaintext format."""
    segments: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            match = LEGACY_SEGMENT_PATTERN.match(line.strip())
            if not match:
                continue
            start_time, end_time, text = match.groups()
            segments.append(
                {
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "text": text,
                }
            )
    logger.info("Parsed {} legacy segments from {}", len(segments), path)
    metadata = {
        "format": "legacy_plaintext",
        "source_file": str(path),
        "schema_version": SCHEMA_VERSION,
    }
    return {"metadata": metadata, "segments": segments}


def parse_transcript(file_path: str | Path) -> dict[str, Any]:
    """
    Load a transcript file and return its metadata and segments.

    Supports both the new JSON schema and the legacy plaintext format to ease
    migration.
    """
    path = Path(file_path)
    logger.info("Parsing transcript file: {}", path)

    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        logger.warning("Detected legacy transcript format at {}", path)
        return _parse_legacy_transcript(path)

    raw_segments: Iterable[Mapping[str, Any]] = (
        data.get("segments") or data.get("transcript") or []
    )
    segments: list[dict[str, Any]] = []
    for raw_segment in raw_segments:
        try:
            segments.append(_normalise_segment(raw_segment))
        except ValueError as exc:
            logger.warning("Skipping malformed segment in {}: {}", path, exc)

    metadata = {
        key: value
        for key, value in (data.get("metadata") or {}).items()
        if value is not None
    }
    metadata.setdefault("format", "json")
    metadata.setdefault("source_file", str(path))
    metadata.setdefault("segment_count", len(segments))
    metadata.setdefault("schema_version", data.get("schema_version", SCHEMA_VERSION))

    logger.info("Parsed {} segments from {}", len(segments), path)
    return {"metadata": metadata, "segments": segments}


def _attach_source(
    segments: Iterable[Mapping[str, Any]], source: str
) -> list[dict[str, Any]]:
    """Copy segments and label them with the originating source."""
    labelled = []
    for segment in segments:
        entry = dict(segment)
        entry["source"] = source
        labelled.append(entry)
    return labelled


def merge_transcripts(
    mic_transcript: Mapping[str, Any],
    desktop_transcript: Mapping[str, Any],
    parse_overlaps: bool = True,
    source_files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge microphone and desktop transcripts into a single structure."""
    logger.info("Merging transcripts")
    mic_segments = _attach_source(mic_transcript.get("segments", []), "microphone")
    desktop_segments = _attach_source(desktop_transcript.get("segments", []), "desktop")

    combined_segments = mic_segments + desktop_segments
    combined_segments.sort(key=lambda item: item["start_time"])

    if not parse_overlaps:
        logger.info("Skipping overlap parsing")
        merged_segments = [dict(segment) for segment in combined_segments]
    else:
        logger.info("Parsing overlaps")
        merged_segments: list[dict[str, Any]] = []
        for segment in combined_segments:
            current = dict(segment)
            if (
                not merged_segments
                or current["start_time"] >= merged_segments[-1]["end_time"]
            ):
                merged_segments.append(current)
                continue

            last_segment = merged_segments[-1]
            overlap_start = current["start_time"]
            overlap_end = min(current["end_time"], last_segment["end_time"])

            merged_segments.append(
                {
                    "start_time": overlap_start,
                    "end_time": overlap_end,
                    "text": (
                        f"[{last_segment['source']}] {last_segment['text']} | "
                        f"[{current['source']}] {current['text']}"
                    ),
                    "source": "overlap",
                }
            )

            if current["end_time"] > last_segment["end_time"]:
                merged_segments.append(
                    {
                        "start_time": last_segment["end_time"],
                        "end_time": current["end_time"],
                        "text": current["text"],
                        "source": current["source"],
                    }
                )

    total_duration = (
        max((segment["end_time"] for segment in merged_segments), default=0.0)
        if combined_segments
        else 0.0
    )
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "parse_overlaps": parse_overlaps,
        "segment_count": len(merged_segments),
        "total_duration": total_duration,
        "sources": {
            "microphone": dict(mic_transcript.get("metadata", {})),
            "desktop": dict(desktop_transcript.get("metadata", {})),
        },
    }
    if source_files is None:
        source_files = {
            "microphone": mic_transcript.get("metadata", {}).get("source_file"),
            "desktop": desktop_transcript.get("metadata", {}).get("source_file"),
        }
    metadata["source_files"] = {
        key: str(Path(value)) if value is not None else None
        for key, value in dict(source_files).items()
    }
    metadata["source_files"] = {
        key: value
        for key, value in metadata["source_files"].items()
        if value is not None
    }

    logger.info("Merged transcript contains {} segments", len(merged_segments))
    return {"metadata": metadata, "transcript": merged_segments}


def save_merged_transcript(
    merged_data: Mapping[str, Any], output_file: str | Path
) -> None:
    logger.info("Saving merged transcript to {}", output_file)
    with Path(output_file).open("w", encoding="utf-8") as handle:
        json.dump(merged_data, handle, indent=2, ensure_ascii=False)
    logger.info("Merged transcript saved successfully")


def process_transcripts(
    mic_transcript_file: str | Path,
    desktop_transcript_file: str | Path,
    output_file: str | Path,
    parse_overlaps: bool = True,
) -> dict[str, Any]:
    logger.info("Starting transcript processing")
    mic_transcript = parse_transcript(mic_transcript_file)
    desktop_transcript = parse_transcript(desktop_transcript_file)

    merged_data = merge_transcripts(
        mic_transcript,
        desktop_transcript,
        parse_overlaps=parse_overlaps,
        source_files={
            "microphone": str(Path(mic_transcript_file)),
            "desktop": str(Path(desktop_transcript_file)),
        },
    )
    save_merged_transcript(merged_data, output_file)

    logger.info("Transcript processing completed. Output saved to {}", output_file)
    return merged_data
