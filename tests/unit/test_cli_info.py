"""Unit tests for the `minutia info` group.

`_list_recordings` is pure logic (glob + sort), TDD'd here. The `info` / `info config` /
`info recordings` command surface is exercised through the CliRunner tests below.
"""

import os

import pytest
from click.testing import CliRunner

import minutia.cli
from minutia import config as config_module
from minutia.cli.info import _list_recordings


class TestListRecordings:
    def test_returns_mkv_newest_first(self, tmp_path):
        older = tmp_path / "older.mkv"
        newer = tmp_path / "newer.mkv"
        older.write_text("o", encoding="utf-8")
        newer.write_text("n", encoding="utf-8")
        # Force a deterministic mtime ordering (older < newer).
        os.utime(older, (1_000, 1_000))
        os.utime(newer, (2_000, 2_000))

        result = _list_recordings(tmp_path)

        assert result == [newer, older]

    def test_ignores_non_mkv(self, tmp_path):
        (tmp_path / "keep.mkv").write_text("v", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
        (tmp_path / "clip.mp4").write_text("y", encoding="utf-8")

        result = _list_recordings(tmp_path)

        assert [p.name for p in result] == ["keep.mkv"]

    def test_empty_when_no_recordings(self, tmp_path):
        assert _list_recordings(tmp_path) == []


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        config_module, "USER_CONFIG_FILE", tmp_path / "user-config" / "config.env"
    )
    for key in list(os.environ):
        if key.startswith("MINUTIA_") or key in {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"}:
            monkeypatch.delenv(key)
    return CliRunner()


class TestInfoCommand:
    def test_bare_info_shows_values_and_sources(self, runner, tmp_path):
        env = {
            "MINUTIA_WHISPER_MODEL": "medium.en",
            "MINUTIA_OUTPUT_DIR": str(tmp_path / "out"),
        }
        result = runner.invoke(minutia.cli.main, ["info"], env=env)
        assert result.exit_code == 0, result.output
        assert "whisper_model = medium.en  [environment]" in result.output
        assert "precedence:" in result.output

    def test_info_config_aliases_bare_info(self, runner, tmp_path):
        env = {"MINUTIA_OUTPUT_DIR": str(tmp_path / "out")}
        bare = runner.invoke(minutia.cli.main, ["info"], env=env)
        alias = runner.invoke(minutia.cli.main, ["info", "config"], env=env)
        assert alias.exit_code == 0, alias.output
        # Same body (ignore the leading loguru init line, which carries a timestamp).
        assert "whisper_model =" in alias.output
        assert (
            alias.output.count("precedence:") == bare.output.count("precedence:") == 1
        )

    def test_info_recordings_lists_newest_first(self, runner, tmp_path):
        recordings = tmp_path / "recordings"
        recordings.mkdir()
        for name, mtime in (("a.mkv", 1_000), ("b.mkv", 2_000)):
            p = recordings / name
            p.write_text("v", encoding="utf-8")
            os.utime(p, (mtime, mtime))

        result = runner.invoke(
            minutia.cli.main,
            ["info", "recordings"],
            env={"MINUTIA_RECORDINGS_DIR": str(recordings)},
        )
        assert result.exit_code == 0, result.output
        # Newest first: b before a.
        assert result.output.index("b.mkv") < result.output.index("a.mkv")

    def test_info_recordings_without_dir_errors(self, runner, tmp_path):
        result = runner.invoke(minutia.cli.main, ["info", "recordings"], env={})
        assert result.exit_code != 0
        assert "MINUTIA_RECORDINGS_DIR" in result.output
