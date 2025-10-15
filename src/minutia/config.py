"""
Configuration loading utilities for the Minutia CLI and pipeline.

This module provides a small configuration system that reads settings from
`.env` files and environment variables using a consistent ``MINUTIA_`` prefix.
It validates basic options, handles Anthropic API key lookup, and exposes a
dataclass that can be threaded through the CLI, pipeline, and supporting
modules.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .paths import CleanupPolicy

# Importing here avoids a circular dependency because pipeline does not import
# this module.
from .pipeline import SUMMARY_MODEL_CHOICES

CONFIG_PREFIX = "MINUTIA_"
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    Path(".env"),
    Path(".minutia"),
)
VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ConfigurationError(ValueError):
    """Raised when configuration values are invalid."""


def _load_env_files(env_file: Path | None) -> None:
    """Load `.env` style files into the process environment."""
    if env_file is not None:
        path = Path(env_file)
        if path.exists():
            load_dotenv(path, override=False)
        return

    for candidate in DEFAULT_ENV_FILES:
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _get_env(env: Mapping[str, str], key: str) -> str | None:
    """Return the environment value for ``key`` with whitespace trimmed."""
    value = env.get(key)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _coerce_int(value: str | None, *, option: str) -> int | None:
    """Convert an optional string value to int, raising a configuration error."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{option} must be an integer (got {value!r})") from exc


def _coerce_path(value: str | None) -> Path | None:
    """Convert an optional string value to a Path instance."""
    if value is None:
        return None
    return Path(value).expanduser()


def resolve_anthropic_api_key(env: Mapping[str, str] | None = None) -> str | None:
    """
    Resolve the Anthropic API key using a fallback chain.

    The loader checks the following locations in order:

    1. ``ANTHROPIC_API_KEY``
    2. ``MINUTIA_ANTHROPIC_API_KEY``
    3. ``CLAUDE_API_KEY`` (legacy)
    """
    env_mapping = env or os.environ
    for key in ("ANTHROPIC_API_KEY", f"{CONFIG_PREFIX}ANTHROPIC_API_KEY", "CLAUDE_API_KEY"):
        value = _get_env(env_mapping, key)
        if value:
            return value
    return None


def _mask_secret(value: str | None) -> str:
    """Return a masked representation of secret values for logs."""
    if not value:
        return "<unset>"
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


@dataclass
class MinutiaConfig:
    """Configuration values used by the CLI and pipeline."""

    whisper_model: str = "base"
    summary_model: str = "claude-4-5-sonnet"
    mic_track: int = 3
    desktop_track: int = 2
    base_output_dir: Path = field(default_factory=lambda: Path("./runs"))
    log_level: str = "INFO"
    cleanup_policy: CleanupPolicy = CleanupPolicy.KEEP_ALL
    anthropic_api_key: str | None = None
    env_sources: Iterable[Path] = field(default_factory=tuple)

    def validate(self) -> None:
        """Validate configuration values and raise ``ConfigurationError`` if invalid."""
        errors = []
        if not self.whisper_model:
            errors.append("whisper_model cannot be empty")
        if self.summary_model not in SUMMARY_MODEL_CHOICES:
            choices = ", ".join(SUMMARY_MODEL_CHOICES)
            errors.append(f"summary_model must be one of: {choices}")
        if self.mic_track < 0:
            errors.append("mic_track must be >= 0")
        if self.desktop_track < 0:
            errors.append("desktop_track must be >= 0")
        if self.log_level.upper() not in VALID_LOG_LEVELS:
            display = ", ".join(sorted(VALID_LOG_LEVELS))
            errors.append(f"log_level must be one of: {display}")
        if not isinstance(self.base_output_dir, Path):
            errors.append("base_output_dir must be a pathlib.Path instance")

        if errors:
            raise ConfigurationError("; ".join(errors))

    @property
    def masked_anthropic_key(self) -> str:
        """Return a masked form of the Anthropic key for logging."""
        return _mask_secret(self.anthropic_api_key)


def load_config(
    *,
    env_file: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> MinutiaConfig:
    """
    Load Minutia configuration from `.env` files and environment variables.

    Parameters
    ----------
    env_file:
        Optional explicit path to a `.env` formatted file. When omitted the
        loader will read `.env` and `.minutia` if they exist.
    env:
        Optional explicit mapping of environment variables (primarily for tests).
    """
    _load_env_files(env_file)
    env_mapping = dict(env or os.environ)

    whisper_model = _get_env(env_mapping, f"{CONFIG_PREFIX}WHISPER_MODEL") or "base"
    summary_model = _get_env(env_mapping, f"{CONFIG_PREFIX}SUMMARY_MODEL") or "claude-4-5-sonnet"
    mic_track = _coerce_int(_get_env(env_mapping, f"{CONFIG_PREFIX}MIC_TRACK"), option="mic_track")
    desktop_track = _coerce_int(
        _get_env(env_mapping, f"{CONFIG_PREFIX}DESKTOP_TRACK"),
        option="desktop_track",
    )
    base_output_dir = _coerce_path(_get_env(env_mapping, f"{CONFIG_PREFIX}OUTPUT_DIR"))
    log_level = (_get_env(env_mapping, f"{CONFIG_PREFIX}LOG_LEVEL") or "INFO").upper()
    cleanup_policy_raw = _get_env(env_mapping, f"{CONFIG_PREFIX}CLEANUP_POLICY")

    if cleanup_policy_raw:
        try:
            cleanup_policy = CleanupPolicy(cleanup_policy_raw)
        except ValueError as exc:
            raise ConfigurationError(f"Unknown cleanup policy: {cleanup_policy_raw!r}") from exc
    else:
        cleanup_policy = CleanupPolicy.KEEP_ALL

    config = MinutiaConfig(
        whisper_model=whisper_model,
        summary_model=summary_model,
        mic_track=mic_track if mic_track is not None else 3,
        desktop_track=desktop_track if desktop_track is not None else 2,
        base_output_dir=base_output_dir or Path("./runs"),
        log_level=log_level,
        cleanup_policy=cleanup_policy,
        anthropic_api_key=resolve_anthropic_api_key(env_mapping),
        env_sources=tuple(DEFAULT_ENV_FILES if env_file is None else (Path(env_file),)),
    )
    config.validate()
    return config


__all__ = [
    "CONFIG_PREFIX",
    "ConfigurationError",
    "MinutiaConfig",
    "load_config",
    "resolve_anthropic_api_key",
]
