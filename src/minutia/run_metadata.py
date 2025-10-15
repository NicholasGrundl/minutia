from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .logging import logger

SCHEMA_VERSION = "1.0"


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _clean_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: MutableMapping[str, Any] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        if isinstance(value, Mapping) and not isinstance(value, str):
            nested = _clean_mapping(value)
            if nested:
                cleaned[str(key)] = nested
        else:
            cleaned[str(key)] = value
    return dict(cleaned)


def build_run_metadata(
    *,
    run_root: Path,
    input_path: Path,
    status: str,
    started_at: datetime,
    completed_at: datetime | None,
    outputs: Mapping[str, Any],
    merged_metadata: Mapping[str, Any] | None = None,
    error: BaseException | None = None,
) -> dict[str, Any]:
    """Construct the run metadata payload according to the MVP schema."""
    input_section: dict[str, Any] = {"source_file": str(input_path)}
    if merged_metadata:
        total_duration = merged_metadata.get("total_duration")
        if total_duration is not None:
            input_section["duration"] = total_duration
        segment_count = merged_metadata.get("segment_count")
        if segment_count is not None:
            input_section["segment_count"] = segment_count

    run_info = {
        "started_at": _isoformat(started_at),
        "completed_at": _isoformat(completed_at),
        "status": status,
    }
    if error is not None:
        run_info["error"] = str(error)

    outputs_section = dict(outputs)
    outputs_section.setdefault("logs", str(run_root / "minutia.log"))

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "run_info": run_info,
        "input": input_section,
        "outputs": outputs_section,
    }

    return _clean_mapping(metadata)


def write_run_metadata(destination: Path, payload: Mapping[str, Any]) -> None:
    """Persist the run metadata payload to disk."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    logger.info("Run metadata written to {}", destination)
