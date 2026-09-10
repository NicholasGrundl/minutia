"""Unit tests for the user-config persistence writer (`write_user_config`).

The wizard's setup flow uses this to persist the recordings dir + the API key into the user
``config.env``. It must merge (never clobber unrelated keys), be idempotent, `chmod 600` (it holds a
secret), and never surface the secret value.
"""

import stat

import pytest

from minutia.config import write_user_config


def _read(path):
    return path.read_text(encoding="utf-8")


def test_creates_file_and_parent_with_values(tmp_path):
    target = tmp_path / "cfg" / "config.env"
    result = write_user_config({"MINUTIA_RECORDINGS_DIR": "/videos"}, path=target)
    assert result == target
    assert target.exists()
    assert "MINUTIA_RECORDINGS_DIR=/videos" in _read(target)


def test_sets_owner_only_permissions(tmp_path):
    target = tmp_path / "config.env"
    write_user_config({"MINUTIA_ANTHROPIC_API_KEY": "sk-ant-secret"}, path=target)
    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode == 0o600


def test_preserves_unrelated_keys_and_comments(tmp_path):
    target = tmp_path / "config.env"
    target.write_text(
        "# my config\nMINUTIA_WHISPER_MODEL=medium.en\nMINUTIA_LOG_LEVEL=INFO\n",
        encoding="utf-8",
    )
    write_user_config({"MINUTIA_RECORDINGS_DIR": "/videos"}, path=target)
    text = _read(target)
    assert "# my config" in text
    assert "MINUTIA_WHISPER_MODEL=medium.en" in text
    assert "MINUTIA_LOG_LEVEL=INFO" in text
    assert "MINUTIA_RECORDINGS_DIR=/videos" in text


def test_updates_existing_key_in_place_without_duplicating(tmp_path):
    target = tmp_path / "config.env"
    target.write_text("MINUTIA_RECORDINGS_DIR=/old\n", encoding="utf-8")
    write_user_config({"MINUTIA_RECORDINGS_DIR": "/new"}, path=target)
    text = _read(target)
    assert "MINUTIA_RECORDINGS_DIR=/new" in text
    assert "/old" not in text
    assert text.count("MINUTIA_RECORDINGS_DIR=") == 1


def test_idempotent_rewrite(tmp_path):
    target = tmp_path / "config.env"
    write_user_config({"MINUTIA_RECORDINGS_DIR": "/videos"}, path=target)
    first = _read(target)
    write_user_config({"MINUTIA_RECORDINGS_DIR": "/videos"}, path=target)
    assert _read(target) == first


def test_does_not_log_the_secret(tmp_path, caplog):
    target = tmp_path / "config.env"
    with caplog.at_level("DEBUG"):
        write_user_config({"MINUTIA_ANTHROPIC_API_KEY": "sk-ant-supersecret"}, path=target)
    assert "sk-ant-supersecret" not in caplog.text


def test_empty_updates_leaves_file_untouched(tmp_path):
    target = tmp_path / "config.env"
    target.write_text("MINUTIA_LOG_LEVEL=INFO\n", encoding="utf-8")
    before = _read(target)
    write_user_config({}, path=target)
    assert _read(target) == before


def test_rejects_newline_in_value(tmp_path):
    target = tmp_path / "config.env"
    with pytest.raises(ValueError, match="newline"):
        write_user_config({"MINUTIA_RECORDINGS_DIR": "a\nb"}, path=target)
