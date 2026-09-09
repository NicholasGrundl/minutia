"""Unit tests for settings resolution, discovery, and input selection."""

import os
from pathlib import Path

import platformdirs
import pytest

from minutia import config as config_module
from minutia.config import ConfigurationError, discover_env_file, resolve_settings
from minutia.paths import resolve_input_video

SETTINGS_ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY",
    "MINUTIA_ANTHROPIC_API_KEY",
    "MINUTIA_CLEANUP_POLICY",
    "MINUTIA_DESKTOP_TRACK",
    "MINUTIA_LOG_LEVEL",
    "MINUTIA_MIC_TRACK",
    "MINUTIA_OUTPUT_DIR",
    "MINUTIA_PERSONAL_INFO",
    "MINUTIA_RECORDINGS_DIR",
    "MINUTIA_SUMMARY_MODEL",
    "MINUTIA_WHISPER_MODEL",
)


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Provide a marked project and isolated persistent config location."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").touch()
    monkeypatch.chdir(project)

    user_config = tmp_path / "user-config" / "config.env"
    monkeypatch.setattr(config_module, "USER_CONFIG_FILE", user_config)
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return {"project": project, "user_config": user_config}


class TestPrecedence:
    def test_environment_beats_context_file_beats_user_config(self, isolated_config):
        paths = isolated_config
        (paths["project"] / ".env").write_text(
            "MINUTIA_WHISPER_MODEL=context-model\nMINUTIA_LOG_LEVEL=DEBUG\n",
            encoding="utf-8",
        )
        paths["user_config"].parent.mkdir(parents=True)
        paths["user_config"].write_text(
            "MINUTIA_WHISPER_MODEL=user-model\n"
            "MINUTIA_LOG_LEVEL=ERROR\n"
            "MINUTIA_MIC_TRACK=7\n",
            encoding="utf-8",
        )

        resolution = resolve_settings(env={"MINUTIA_WHISPER_MODEL": "env-model"})
        settings = resolution.settings

        assert settings.whisper_model == "env-model"
        assert resolution.sources["whisper_model"] == "environment"
        assert settings.log_level == "DEBUG"
        assert resolution.sources["log_level"] == str(paths["project"] / ".env")
        assert settings.mic_track == 7
        assert resolution.sources["mic_track"] == str(paths["user_config"])

    def test_higher_source_wins_across_different_api_key_aliases(self, isolated_config):
        paths = isolated_config
        paths["user_config"].parent.mkdir(parents=True)
        paths["user_config"].write_text(
            "ANTHROPIC_API_KEY=user-key\n", encoding="utf-8"
        )
        (paths["project"] / ".env").write_text(
            "MINUTIA_ANTHROPIC_API_KEY=context-key\n", encoding="utf-8"
        )

        resolution = resolve_settings(env={"CLAUDE_API_KEY": "environment-key"})

        assert resolution.settings.anthropic_api_key == "environment-key"
        assert resolution.sources["anthropic_api_key"] == "environment"

    def test_alias_order_is_deterministic_within_one_source(self, isolated_config):
        settings = resolve_settings(
            env={
                "CLAUDE_API_KEY": "legacy-key",
                "MINUTIA_ANTHROPIC_API_KEY": "prefixed-key",
                "ANTHROPIC_API_KEY": "provider-key",
            }
        ).settings

        assert settings.anthropic_api_key == "provider-key"

    def test_defaults_and_sources_when_nothing_configured(self, isolated_config):
        resolution = resolve_settings(env={})
        settings = resolution.settings

        assert settings.whisper_model == "base"
        assert resolution.sources["whisper_model"] == "default"
        assert settings.mic_track == 3
        assert settings.recordings_dir is None
        assert settings.personal_info_path is None

    def test_output_dir_defaults_to_documents_minutia(self, isolated_config):
        resolution = resolve_settings(env={})

        assert (
            resolution.settings.base_output_dir
            == platformdirs.user_documents_path() / "minutia"
        )
        assert resolution.sources["base_output_dir"] == "default"


class TestDotenvDiscovery:
    def test_finds_nearest_env_file_from_nested_invocation(self, tmp_path):
        project = tmp_path / "project"
        nested = project / "src" / "pkg"
        nested.mkdir(parents=True)
        (project / ".git").mkdir()
        expected = project / ".env"
        expected.touch()

        assert discover_env_file(nested, home_dir=tmp_path / "home") == expected

    def test_stops_at_project_boundary_when_no_env_file_exists(self, tmp_path):
        project = tmp_path / "project"
        nested = project / "nested"
        nested.mkdir(parents=True)
        (project / "pyproject.toml").touch()
        (tmp_path / ".env").touch()

        assert discover_env_file(nested, home_dir=tmp_path / "home") is None

    def test_does_not_implicitly_load_home_env_file(self, tmp_path):
        home = tmp_path / "home"
        child = home / "work"
        child.mkdir(parents=True)
        (home / ".env").touch()

        assert discover_env_file(child, home_dir=home) is None

    def test_explicit_env_file_bypasses_discovery(self, isolated_config, tmp_path):
        project = isolated_config["project"]
        (project / ".env").write_text(
            "MINUTIA_WHISPER_MODEL=discovered\n", encoding="utf-8"
        )
        explicit = tmp_path / "chosen.env"
        explicit.write_text("MINUTIA_WHISPER_MODEL=explicit\n", encoding="utf-8")

        resolution = resolve_settings(env_file=explicit, env={})

        assert resolution.settings.whisper_model == "explicit"
        assert resolution.context_env_file == explicit

    def test_discovery_can_be_disabled(self, isolated_config):
        project = isolated_config["project"]
        (project / ".env").write_text(
            "MINUTIA_WHISPER_MODEL=discovered\n", encoding="utf-8"
        )

        resolution = resolve_settings(env={}, discover_dotenv=False)

        assert resolution.settings.whisper_model == "base"
        assert resolution.context_env_file is None

    def test_explicit_missing_env_file_errors(self, isolated_config):
        with pytest.raises(ConfigurationError, match="does not exist"):
            resolve_settings(env_file=Path("missing.env"), env={})

    def test_legacy_dot_minutia_file_is_ignored(self, isolated_config):
        project = isolated_config["project"]
        (project / ".minutia").write_text(
            "MINUTIA_WHISPER_MODEL=legacy\n", encoding="utf-8"
        )

        settings = resolve_settings(env={}).settings

        assert settings.whisper_model == "base"


class TestPathResolution:
    def test_file_paths_are_relative_to_the_file_that_declared_them(
        self, isolated_config
    ):
        paths = isolated_config
        paths["user_config"].parent.mkdir(parents=True)
        paths["user_config"].write_text(
            "MINUTIA_OUTPUT_DIR=global-runs\n", encoding="utf-8"
        )
        (paths["project"] / ".env").write_text(
            "MINUTIA_RECORDINGS_DIR=recordings\n", encoding="utf-8"
        )

        settings = resolve_settings(env={}).settings

        assert settings.base_output_dir == paths["user_config"].parent / "global-runs"
        assert settings.recordings_dir == paths["project"] / "recordings"

    def test_environment_paths_are_relative_to_invocation_dir(self, isolated_config):
        project = isolated_config["project"]

        settings = resolve_settings(
            env={"MINUTIA_PERSONAL_INFO": "context/me.md"}
        ).settings

        assert settings.personal_info_path == project / "context" / "me.md"

    def test_tilde_paths_expand_before_source_anchoring(
        self, isolated_config, monkeypatch, tmp_path
    ):
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        settings = resolve_settings(
            env={"MINUTIA_RECORDINGS_DIR": "~/recordings"}
        ).settings

        assert settings.recordings_dir == fake_home / "recordings"


class TestValidationAndIsolation:
    def test_invalid_values_raise_configuration_error(self, isolated_config):
        with pytest.raises(ConfigurationError, match="greater than or equal to 0"):
            resolve_settings(env={"MINUTIA_MIC_TRACK": "-1"})

        with pytest.raises(ConfigurationError, match="log_level must be one of"):
            resolve_settings(env={"MINUTIA_LOG_LEVEL": "verbose"})

        with pytest.raises(ConfigurationError, match="summary_model must be one of"):
            resolve_settings(env={"MINUTIA_SUMMARY_MODEL": "made-up-model"})

    def test_loading_dotenv_does_not_mutate_process_environment(
        self, isolated_config, monkeypatch
    ):
        key = "MINUTIA_WHISPER_MODEL"
        monkeypatch.delenv(key, raising=False)
        (isolated_config["project"] / ".env").write_text(
            f"{key}=from-file\n", encoding="utf-8"
        )

        settings = resolve_settings().settings

        assert settings.whisper_model == "from-file"
        assert key not in os.environ

    def test_empty_explicit_environment_mapping_does_not_fall_back_to_ambient(
        self, isolated_config, monkeypatch
    ):
        monkeypatch.setenv("MINUTIA_WHISPER_MODEL", "ambient")

        settings = resolve_settings(env={}).settings

        assert settings.whisper_model == "base"


class TestResolveInputVideo:
    def test_explicit_path_wins(self, tmp_path):
        explicit = tmp_path / "given.mkv"
        explicit.write_text("x", encoding="utf-8")
        recordings = tmp_path / "recordings"
        recordings.mkdir()
        (recordings / "other.mkv").write_text("y", encoding="utf-8")
        assert resolve_input_video(explicit, recordings) == explicit

    def test_picks_newest_mkv_by_mtime(self, tmp_path):
        recordings = tmp_path / "recordings"
        recordings.mkdir()
        old = recordings / "old.mkv"
        new = recordings / "new.mkv"
        old.write_text("a", encoding="utf-8")
        new.write_text("b", encoding="utf-8")
        os.utime(old, (1_000_000, 1_000_000))
        os.utime(new, (2_000_000, 2_000_000))
        assert resolve_input_video(None, recordings) == new

    def test_errors_when_recordings_dir_unset(self):
        with pytest.raises(ConfigurationError, match="MINUTIA_RECORDINGS_DIR"):
            resolve_input_video(None, None)

    def test_errors_when_recordings_dir_missing(self, tmp_path):
        with pytest.raises(ConfigurationError, match="does not exist"):
            resolve_input_video(None, tmp_path / "nope")

    def test_errors_when_no_mkv_files(self, tmp_path):
        recordings = tmp_path / "recordings"
        recordings.mkdir()
        with pytest.raises(ConfigurationError, match="No .mkv"):
            resolve_input_video(None, recordings)
