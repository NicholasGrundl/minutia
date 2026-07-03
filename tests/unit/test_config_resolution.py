"""Unit tests for layered config resolution, source tracking, and input discovery."""

import os

import platformdirs
import pytest

from minutia import config as config_module
from minutia.config import ConfigurationError, load_config
from minutia.paths import resolve_input_video

pytestmark = pytest.mark.unit


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Run config loading against a temp CWD and a temp user-config file."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    user_config = tmp_path / "userconfig" / "config.env"
    monkeypatch.setattr(config_module, "USER_CONFIG_FILE", user_config)
    # Keep ambient MINUTIA_* vars out of the environment layer.
    for key in list(os.environ):
        if key.startswith("MINUTIA_"):
            monkeypatch.delenv(key)
    return {"cwd": cwd, "user_config": user_config}


class TestPrecedence:
    def test_env_beats_cwd_env_file_beats_user_config(self, isolated_config):
        paths = isolated_config
        (paths["cwd"] / ".env").write_text(
            "MINUTIA_WHISPER_MODEL=cwd-model\nMINUTIA_LOG_LEVEL=DEBUG\n",
            encoding="utf-8",
        )
        paths["user_config"].parent.mkdir(parents=True)
        paths["user_config"].write_text(
            "MINUTIA_WHISPER_MODEL=user-model\n"
            "MINUTIA_LOG_LEVEL=ERROR\n"
            "MINUTIA_MIC_TRACK=7\n",
            encoding="utf-8",
        )

        cfg = load_config(env={"MINUTIA_WHISPER_MODEL": "env-model"})

        assert cfg.whisper_model == "env-model"
        assert cfg.sources["whisper_model"] == "environment"
        assert cfg.log_level == "DEBUG"
        assert cfg.sources["log_level"].endswith(".env")
        assert cfg.mic_track == 7
        assert str(paths["user_config"]) in cfg.sources["mic_track"]

    def test_defaults_and_sources_when_nothing_configured(self, isolated_config):
        cfg = load_config(env={})
        assert cfg.whisper_model == "base"
        assert cfg.sources["whisper_model"] == "default"
        assert cfg.mic_track == 3
        assert cfg.recordings_dir is None
        assert cfg.personal_info_path is None

    def test_output_dir_defaults_to_documents_minutia(self, isolated_config):
        cfg = load_config(env={})
        assert cfg.base_output_dir == platformdirs.user_documents_path() / "minutia"
        assert cfg.sources["base_output_dir"] == "default"

    def test_recordings_dir_from_user_config(self, isolated_config):
        paths = isolated_config
        paths["user_config"].parent.mkdir(parents=True)
        paths["user_config"].write_text(
            "MINUTIA_RECORDINGS_DIR=~/recordings\n", encoding="utf-8"
        )
        cfg = load_config(env={})
        assert cfg.recordings_dir == config_module.Path.home() / "recordings"
        assert str(paths["user_config"]) in cfg.sources["recordings_dir"]


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
