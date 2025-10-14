"""
Unified logging configuration for the Minutia pipeline.

This module wraps Loguru to provide a single logging surface with contextual
fields that can be shared across all pipeline components. The configuration
adds both a coloured stderr sink for developer feedback and, when available, a
file sink placed inside the active run directory.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from loguru import logger as _logger

ContextValue = Union[str, Path]

_CONTEXT_DEFAULTS = {"step": "-", "input_file": "-", "run_root": "-"}


def _normalise_context_value(value: ContextValue) -> str:
    """Return a string representation for context values."""
    if isinstance(value, Path):
        return str(value)
    return value


def _format_record(record: dict) -> str:
    """Inject contextual defaults before formatting a log record."""
    extra = record.setdefault("extra", {})
    for key, default in _CONTEXT_DEFAULTS.items():
        if key not in extra or not extra[key]:
            extra[key] = default
        else:
            extra[key] = _normalise_context_value(extra[key])
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level:<8}</level> | "
        "{extra[step]:<16} | "
        "{extra[input_file]} | "
        "{extra[run_root]} | "
        "{message}"
    )


def configure_logging(
    *,
    level: str = "INFO",
    logs_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Configure loguru sinks for the current process.

    Parameters
    ----------
    level:
        Minimum log level for the stderr sink.
    logs_file:
        Optional path for a run-scoped log file.
    """
    _logger.remove()
    _logger.configure(extra=_CONTEXT_DEFAULTS.copy())

    _logger.add(
        sys.stderr,
        level=level.upper(),
        colorize=True,
        backtrace=False,
        diagnose=False,
        format=_format_record,
    )

    if logs_file:
        path = Path(logs_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        _logger.add(
            path,
            level="DEBUG",
            rotation=None,
            retention=None,
            enqueue=False,
            format=_format_record,
        )


@contextmanager
def logging_context(
    *,
    step: Optional[str] = None,
    input_file: Optional[ContextValue] = None,
    run_root: Optional[ContextValue] = None,
) -> Generator[None, None, None]:
    """
    Temporarily enrich log records with contextual fields.

    Parameters
    ----------
    step:
        Name of the active pipeline step.
    input_file:
        Primary input path for the pipeline run.
    run_root:
        Root directory for run artifacts.
    """
    context = {}
    if step is not None:
        context["step"] = step
    if input_file is not None:
        context["input_file"] = _normalise_context_value(input_file)
    if run_root is not None:
        context["run_root"] = _normalise_context_value(run_root)

    if not context:
        yield
        return

    with _logger.contextualize(**context):
        yield


# Expose the configured logger for callers to import directly.
logger = _logger

