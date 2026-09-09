"""Validated settings resolution for the Minutia CLI.

Application settings are resolved, from lowest to highest precedence, from
built-in defaults, the platformdirs user config, one contextual ``.env`` file,
and the process environment. Command-specific CLI arguments are applied by the
CLI after this module returns the validated settings.

Dotenv files are read as data. They are never loaded into ``os.environ``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar

import platformdirs
from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource

from .model_registry import DEFAULT_SUMMARY_MODEL, anthropic_models
from .paths import CleanupPolicy

CONFIG_PREFIX = "MINUTIA_"
USER_CONFIG_FILE: Path = platformdirs.user_config_path("minutia") / "config.env"
DEFAULT_OUTPUT_DIR: Path = platformdirs.user_documents_path() / "minutia"
VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
PROJECT_MARKERS = (".git", "pyproject.toml")

DEFAULT_SOURCE = "default"
ENVIRONMENT_SOURCE = "environment"

_PATH_FIELDS = {"base_output_dir", "recordings_dir", "personal_info_path"}


class ConfigurationError(ValueError):
    """Raised when configuration discovery or validation fails."""


class MinutiaSettings(BaseSettings):
    """Validated application settings used by the CLI and pipeline boundary."""

    model_config = SettingsConfigDict(
        env_prefix=CONFIG_PREFIX,
        env_file=None,
        env_ignore_empty=True,
        extra="ignore",
        populate_by_name=True,
        validate_default=True,
    )

    whisper_model: str = Field(default="base", validation_alias="MINUTIA_WHISPER_MODEL")
    summary_model: str = Field(
        default=DEFAULT_SUMMARY_MODEL,
        validation_alias="MINUTIA_SUMMARY_MODEL",
    )
    mic_track: int = Field(default=3, ge=0, validation_alias="MINUTIA_MIC_TRACK")
    desktop_track: int = Field(
        default=2, ge=0, validation_alias="MINUTIA_DESKTOP_TRACK"
    )
    base_output_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
        validation_alias="MINUTIA_OUTPUT_DIR",
    )
    recordings_dir: Path | None = Field(
        default=None,
        validation_alias="MINUTIA_RECORDINGS_DIR",
    )
    personal_info_path: Path | None = Field(
        default=None,
        validation_alias="MINUTIA_PERSONAL_INFO",
    )
    log_level: str = Field(default="INFO", validation_alias="MINUTIA_LOG_LEVEL")
    cleanup_policy: CleanupPolicy = Field(
        default=CleanupPolicy.KEEP_ALL,
        validation_alias="MINUTIA_CLEANUP_POLICY",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "ANTHROPIC_API_KEY",
            "MINUTIA_ANTHROPIC_API_KEY",
            "CLAUDE_API_KEY",
        ),
    )

    _summary_model_choices: ClassVar[tuple[str, ...]] = tuple(anthropic_models)

    @field_validator("whisper_model")
    @classmethod
    def _validate_whisper_model(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("whisper_model cannot be empty")
        return value

    @field_validator("summary_model")
    @classmethod
    def _validate_summary_model(cls, value: str) -> str:
        value = value.strip()
        if value not in cls._summary_model_choices:
            choices = ", ".join(cls._summary_model_choices)
            raise ValueError(f"summary_model must be one of: {choices}")
        return value

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in VALID_LOG_LEVELS:
            choices = ", ".join(sorted(VALID_LOG_LEVELS))
            raise ValueError(f"log_level must be one of: {choices}")
        return value

    @property
    def masked_anthropic_key(self) -> str:
        """Return a masked form of the Anthropic key for display and logs."""
        return _mask_secret(self.anthropic_api_key)


@dataclass(frozen=True)
class SettingsResolution:
    """Validated settings plus observable source-resolution metadata."""

    settings: MinutiaSettings
    sources: Mapping[str, str]
    invocation_dir: Path
    context_env_file: Path | None
    user_config_file: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))


def discover_env_file(
    invocation_dir: Path | None = None,
    *,
    home_dir: Path | None = None,
) -> Path | None:
    """Find the nearest contextual ``.env`` without crossing a safe boundary.

    The current directory is checked first. The search stops after checking the
    first directory containing ``.git`` or ``pyproject.toml``. A user's home
    directory and the filesystem root are never checked implicitly.
    """
    current = _absolute_path(invocation_dir or Path.cwd(), Path.cwd())
    home = _absolute_path(home_dir or Path.home(), Path.cwd())

    while current != home and current.parent != current:
        candidate = current / ".env"
        if candidate.is_file():
            return candidate
        if any((current / marker).exists() for marker in PROJECT_MARKERS):
            return None
        current = current.parent
    return None


def resolve_settings(
    *,
    env_file: Path | None = None,
    env: Mapping[str, str] | None = None,
    invocation_dir: Path | None = None,
    discover_dotenv: bool = True,
) -> SettingsResolution:
    """Resolve and validate settings without mutating the process environment.

    ``env`` is an explicit environment mapping primarily useful to embedded
    callers and tests. Passing an empty mapping intentionally disables ambient
    process-environment values while retaining file-based settings.
    """
    anchor = _absolute_path(invocation_dir or Path.cwd(), Path.cwd())
    selected_env = _select_env_file(
        env_file=env_file,
        invocation_dir=anchor,
        discover_dotenv=discover_dotenv,
    )
    user_config = _absolute_path(USER_CONFIG_FILE, anchor)

    values = _default_values()
    sources = dict.fromkeys(values, DEFAULT_SOURCE)

    if user_config.is_file():
        _overlay(values, sources, _dotenv_values(user_config), str(user_config))
    if selected_env is not None and selected_env != user_config:
        _overlay(values, sources, _dotenv_values(selected_env), str(selected_env))

    environment_values = (
        _environment_values() if env is None else _values_from_environment_mapping(env)
    )
    _overlay(values, sources, environment_values, ENVIRONMENT_SOURCE)
    _anchor_relative_paths(values, sources, anchor)

    try:
        # Every field is supplied explicitly, so BaseSettings' normal environment
        # source cannot re-enter and bypass the source composition above.
        settings = MinutiaSettings(_env_file=None, **values)
    except ValidationError as exc:
        raise ConfigurationError(_format_validation_error(exc)) from exc

    return SettingsResolution(
        settings=settings,
        sources=sources,
        invocation_dir=anchor,
        context_env_file=selected_env,
        user_config_file=user_config,
    )


def _select_env_file(
    *,
    env_file: Path | None,
    invocation_dir: Path,
    discover_dotenv: bool,
) -> Path | None:
    if env_file is not None:
        selected = _absolute_path(env_file, invocation_dir)
        if not selected.is_file():
            raise ConfigurationError(f"Environment file does not exist: {selected}")
        return selected
    if not discover_dotenv:
        return None
    return discover_env_file(invocation_dir)


def _default_values() -> dict[str, Any]:
    return {
        field_name: field.get_default(call_default_factory=True)
        for field_name, field in MinutiaSettings.model_fields.items()
    }


def _dotenv_values(path: Path) -> dict[str, Any]:
    source = DotEnvSettingsSource(
        MinutiaSettings,
        env_file=path,
        env_file_encoding="utf-8",
        dotenv_filtering="only_existing",
        env_ignore_empty=True,
    )
    return _canonicalize_source(source())


def _environment_values() -> dict[str, Any]:
    source = EnvSettingsSource(MinutiaSettings, env_ignore_empty=True)
    return _canonicalize_source(source())


def _values_from_environment_mapping(env: Mapping[str, str]) -> dict[str, Any]:
    """Read known settings aliases from an explicit, case-insensitive mapping."""
    normalized = {key.lower(): value for key, value in env.items()}
    values: dict[str, Any] = {}
    for field_name, field in MinutiaSettings.model_fields.items():
        for env_name in _field_environment_names(field_name, field):
            value = normalized.get(env_name.lower())
            if value is not None and (not isinstance(value, str) or value.strip()):
                values[field_name] = value
                break
    return values


def _canonicalize_source(source: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for source_name, value in source.items():
        field_name = _field_name_for_source_key(source_name)
        if field_name is not None:
            values[field_name] = value
    return values


def _field_name_for_source_key(source_key: str) -> str | None:
    if source_key in MinutiaSettings.model_fields:
        return source_key
    normalized = source_key.lower()
    for field_name, field in MinutiaSettings.model_fields.items():
        if any(
            normalized == env_name.lower()
            for env_name in _field_environment_names(field_name, field)
        ):
            return field_name
    return None


def _field_environment_names(field_name: str, field: FieldInfo) -> tuple[str, ...]:
    alias = field.validation_alias
    if isinstance(alias, AliasChoices):
        return tuple(str(choice) for choice in alias.choices)
    if isinstance(alias, str):
        return (alias,)
    return (f"{CONFIG_PREFIX}{field_name.upper()}",)


def _overlay(
    values: dict[str, Any],
    sources: dict[str, str],
    incoming: Mapping[str, Any],
    source_name: str,
) -> None:
    for field_name, value in incoming.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        values[field_name] = value
        sources[field_name] = source_name


def _anchor_relative_paths(
    values: dict[str, Any], sources: Mapping[str, str], invocation_dir: Path
) -> None:
    for field_name in _PATH_FIELDS:
        raw_value = values.get(field_name)
        if raw_value is None:
            continue
        path = Path(raw_value).expanduser()
        if path.is_absolute():
            values[field_name] = path
            continue

        source = sources[field_name]
        anchor = (
            Path(source).parent
            if source not in {DEFAULT_SOURCE, ENVIRONMENT_SOURCE}
            else invocation_dir
        )
        values[field_name] = (anchor / path).resolve()


def _absolute_path(path: Path, anchor: Path) -> Path:
    path = Path(path).expanduser()
    return path.resolve() if path.is_absolute() else (anchor / path).resolve()


def _format_validation_error(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}")
    return "; ".join(messages)


def _mask_secret(value: str | None) -> str:
    if not value:
        return "<unset>"
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


__all__ = [
    "CONFIG_PREFIX",
    "DEFAULT_OUTPUT_DIR",
    "USER_CONFIG_FILE",
    "ConfigurationError",
    "MinutiaSettings",
    "SettingsResolution",
    "discover_env_file",
    "resolve_settings",
]
