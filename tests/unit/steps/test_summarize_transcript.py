"""Unit tests for the report helpers in minutia.steps.summarize_transcript."""

import pytest

from minutia.steps import summarize_transcript


def test_get_filename_from_content_returns_model_text(mock_llm):
    mock_llm.set_responses(["20260702_test_meeting_summary"])
    result = summarize_transcript.get_filename_from_content(
        "some summary content", api_key="fake-api-key"
    )
    assert result == "20260702_test_meeting_summary"
    # The filename prompt (not the raw content alone) must be what was sent.
    (call,) = mock_llm.calls
    assert "filenamerules" in call["messages"][0]["content"]
    assert "some summary content" in call["messages"][0]["content"]


def test_get_filename_from_content_unknown_model_raises(mock_llm):
    with pytest.raises(KeyError):
        summarize_transcript.get_filename_from_content(
            "content", model_name="not-a-model", api_key="fake-api-key"
        )
    assert mock_llm.calls == []


def test_get_filename_from_content_default_model_is_valid(mock_llm):
    summarize_transcript.get_filename_from_content("content", api_key="fake-api-key")
    (call,) = mock_llm.calls
    valid_api_names = {
        info["name"] for info in summarize_transcript.anthropic_models.values()
    }
    assert call["model"] in valid_api_names


def test_create_markdown_report_writes_file_with_generated_name(mock_llm, tmp_path):
    mock_llm.set_responses(["20260702_project_kickoff"])
    content = "# Meeting Summary\n\nDetails here."
    filepath = summarize_transcript.create_markdown_report(
        content, tmp_path, api_key="fake-api-key"
    )
    assert filepath == tmp_path / "20260702_project_kickoff.md"
    assert filepath.read_text(encoding="utf-8") == content
