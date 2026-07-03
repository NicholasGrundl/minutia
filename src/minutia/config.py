"""
Configuration loading utilities for the Minutia CLI and pipeline.

This module provides a small configuration system that reads settings using a
consistent ``MINUTIA_`` prefix from layered sources, in precedence order:

1. Process environment variables
2. CWD env files (``.env``, then ``.minutia``)
3. The user-global config file (``platformdirs.user_config_path('minutia')/config.env``)
4. Built-in defaults (output home is ``platformdirs.user_documents_path()/minutia``)

Each resolved value records which layer supplied it (``MinutiaConfig.sources``),
which drives the ``minutia config`` command's provenance display.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import platformdirs
from dotenv import dotenv_values, load_dotenv

from .model_registry import DEFAULT_SUMMARY_MODEL
from .paths import CleanupPolicy

# Importing here avoids a circular dependency because pipeline does not import
# this module.
from .pipeline.orchestrator import SUMMARY_MODEL_CHOICES

CONFIG_PREFIX = "MINUTIA_"
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    Path(".env"),
    Path(".minutia"),
)
USER_CONFIG_FILE: Path = platformdirs.user_config_path("minutia") / "config.env"
DEFAULT_OUTPUT_DIR: Path = platformdirs.user_documents_path() / "minutia"
VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

DEFAULT_SOURCE = "default"
ENVIRONMENT_SOURCE = "environment"


class ConfigurationError(ValueError):
    """Raised when configuration values are invalid."""


def _load_env_files(env_file: Path | None) -> None:
    """Load env files into the process environment (earlier wins; env always wins).

    Kept for backwards compatibility: downstream code (e.g.
    ``resolve_anthropic_api_key`` called without an explicit mapping) reads
    ``os.environ`` and expects dotenv values to be present there.
    """
    if env_file is not None:
        path = Path(env_file)
        if path.exists():
            load_dotenv(path, override=False)
        return

    for candidate in (*DEFAULT_ENV_FILES, USER_CONFIG_FILE):
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _file_values(path: Path) -> dict[str, str]:
    """Read an env-format file into a mapping, dropping unset values."""
    return {k: v for k, v in dotenv_values(path).items() if v is not None}


def _config_layers(
    env_mapping: Mapping[str, str], env_file: Path | None
) -> list[tuple[str, Mapping[str, str]]]:
    """Build the precedence-ordered (source-name, mapping) layers."""
    layers: list[tuple[str, Mapping[str, str]]] = [(ENVIRONMENT_SOURCE, env_mapping)]
    if env_file is not None:
        path = Path(env_file)
        if path.exists():
            layers.append((str(path), _file_values(path)))
        return layers

    for candidate in DEFAULT_ENV_FILES:
        if candidate.exists():
            layers.append((str(candidate), _file_values(candidate)))
    if USER_CONFIG_FILE.exists():
        layers.append((str(USER_CONFIG_FILE), _file_values(USER_CONFIG_FILE)))
    return layers


def _resolve(
    layers: Iterable[tuple[str, Mapping[str, str]]], key: str
) -> tuple[str | None, str]:
    """Return (value, source-name) for ``key``, walking layers in precedence order."""
    for source, mapping in layers:
        value = mapping.get(key)
        if value is not None and value.strip():
            return value.strip(), source
    return None, DEFAULT_SOURCE


def _coerce_int(value: str | None, *, option: str) -> int | None:
    """Convert an optional string value to int, raising a configuration error."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"{option} must be an integer (got {value!r})"
        ) from exc


def _coerce_path(value: str | None) -> Path | None:
    """Convert an optional string value to an expanded Path instance."""
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
    for key in (
        "ANTHROPIC_API_KEY",
        f"{CONFIG_PREFIX}ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
    ):
        value = env_mapping.get(key)
        if value and value.strip():
            return value.strip()
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
    summary_model: str = DEFAULT_SUMMARY_MODEL
    mic_track: int = 3
    desktop_track: int = 2
    base_output_dir: Path = field(default_factory=lambda: DEFAULT_OUTPUT_DIR)
    recordings_dir: Path | None = None
    personal_info_path: Path | None = None
    log_level: str = "INFO"
    cleanup_policy: CleanupPolicy = CleanupPolicy.KEEP_ALL
    anthropic_api_key: str | None = None
    env_sources: Iterable[Path] = field(default_factory=tuple)
    sources: dict[str, str] = field(default_factory=dict)

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
    Load Minutia configuration from layered sources with provenance tracking.

    Parameters
    ----------
    env_file:
        Optional explicit path to a `.env` formatted file. When omitted the
        loader reads CWD `.env` / `.minutia` and the user-global config file.
    env:
        Optional explicit mapping of environment variables (primarily for tests).
    """
    _load_env_files(env_file)
    env_mapping = dict(env if env is not None else os.environ)
    layers = _config_layers(env_mapping, env_file)

    sources: dict[str, str] = {}

    def resolved(option: str, key: str) -> str | None:
        value, source = _resolve(layers, f"{CONFIG_PREFIX}{key}")
        sources[option] = source
        return value

    whisper_model = resolved("whisper_model", "WHISPER_MODEL") or "base"
    summary_model = resolved("summary_model", "SUMMARY_MODEL") or DEFAULT_SUMMARY_MODEL
    mic_track = _coerce_int(resolved("mic_track", "MIC_TRACK"), option="mic_track")
    desktop_track = _coerce_int(
        resolved("desktop_track", "DESKTOP_TRACK"), option="desktop_track"
    )
    base_output_dir = _coerce_path(resolved("base_output_dir", "OUTPUT_DIR"))
    recordings_dir = _coerce_path(resolved("recordings_dir", "RECORDINGS_DIR"))
    personal_info_path = _coerce_path(resolved("personal_info_path", "PERSONAL_INFO"))
    log_level = (resolved("log_level", "LOG_LEVEL") or "INFO").upper()
    cleanup_policy_raw = resolved("cleanup_policy", "CLEANUP_POLICY")

    if cleanup_policy_raw:
        try:
            cleanup_policy = CleanupPolicy(cleanup_policy_raw)
        except ValueError as exc:
            raise ConfigurationError(
                f"Unknown cleanup policy: {cleanup_policy_raw!r}"
            ) from exc
    else:
        cleanup_policy = CleanupPolicy.KEEP_ALL

    # The API key checks three variable names in priority order, each across
    # all layers (so a key set only in the user config file still resolves).
    anthropic_api_key: str | None = None
    sources["anthropic_api_key"] = DEFAULT_SOURCE
    for key_name in (
        "ANTHROPIC_API_KEY",
        f"{CONFIG_PREFIX}ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
    ):
        value, source = _resolve(layers, key_name)
        if value:
            anthropic_api_key = value
            sources["anthropic_api_key"] = source
            break

    config = MinutiaConfig(
        whisper_model=whisper_model,
        summary_model=summary_model,
        mic_track=mic_track if mic_track is not None else 3,
        desktop_track=desktop_track if desktop_track is not None else 2,
        base_output_dir=base_output_dir or DEFAULT_OUTPUT_DIR,
        recordings_dir=recordings_dir,
        personal_info_path=personal_info_path,
        log_level=log_level,
        cleanup_policy=cleanup_policy,
        anthropic_api_key=anthropic_api_key,
        env_sources=tuple(DEFAULT_ENV_FILES if env_file is None else (Path(env_file),)),
        sources=sources,
    )
    config.validate()
    return config


__all__ = [
    "CONFIG_PREFIX",
    "DEFAULT_OUTPUT_DIR",
    "USER_CONFIG_FILE",
    "ConfigurationError",
    "MinutiaConfig",
    "load_config",
    "resolve_anthropic_api_key",
]
