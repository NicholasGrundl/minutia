"""Unit tests for the loguru configuration in `minutia.logging`.

Regression: the sinks use a callable format, and loguru only appends the line
terminator itself for string formats. Without an explicit newline every record
ran into whatever was printed next (first seen as `minutia info` output glued to
the "CLI initialised" log line).
"""

import pytest

from minutia.logging import configure_logging, logger


@pytest.fixture
def restore_logging():
    yield
    logger.remove()


class TestRecordTermination:
    def test_stderr_records_end_with_newline(self, capsys, restore_logging):
        configure_logging(level="INFO")

        logger.info("first")
        logger.info("second")

        lines = capsys.readouterr().err.splitlines()
        assert len(lines) == 2
        assert "first" in lines[0] and "second" not in lines[0]
        assert "second" in lines[1]

    def test_file_records_are_one_per_line(self, tmp_path, restore_logging):
        logs_file = tmp_path / "logs" / "run.log"
        configure_logging(level="INFO", logs_file=logs_file)

        logger.info("first")
        logger.info("second")

        content = logs_file.read_text(encoding="utf-8")
        assert content.endswith("\n")
        assert len(content.splitlines()) == 2

    def test_exception_logs_one_line_without_traceback(self, capsys, restore_logging):
        configure_logging(level="INFO")

        try:
            raise ValueError("boom")
        except ValueError as exc:
            logger.exception("failed: {}", exc)

        lines = capsys.readouterr().err.splitlines()
        assert len(lines) == 1
        assert "failed: boom" in lines[0]
