"""Unit tests for the prompt registry in minutia.prompts."""

import pytest

from minutia import prompts

pytestmark = pytest.mark.unit

EXPECTED_KINDS = {
    "baseline",
    "realtor",
    "minutia",
    "slide-review",
    "interview-debrief",
    "discovery-summary",
}

NOTES_SENTINEL = "SENTINEL-NOTES-a1b2c3"
INFO_SENTINEL = "SENTINEL-INFO-x9y8z7"


def test_list_prompt_kinds_returns_all_kinds():
    assert set(prompts.list_prompt_kinds()) == EXPECTED_KINDS


@pytest.mark.parametrize("kind", sorted(EXPECTED_KINDS))
def test_every_kind_renders_with_context(kind):
    builder = prompts.get_prompt_builder(kind)
    rendered = builder(markdown_notes=NOTES_SENTINEL, personal_info=INFO_SENTINEL)
    assert isinstance(rendered, str)
    assert NOTES_SENTINEL in rendered
    assert INFO_SENTINEL in rendered


@pytest.mark.parametrize("kind", sorted(EXPECTED_KINDS))
def test_every_kind_renders_without_context(kind):
    builder = prompts.get_prompt_builder(kind)
    rendered = builder()
    assert isinstance(rendered, str)
    assert len(rendered) > 100


def test_get_prompt_builder_none_returns_default():
    assert prompts.DEFAULT_PROMPT_KIND in EXPECTED_KINDS
    builder = prompts.get_prompt_builder(None)
    assert builder is prompts.PROMPT_BUILDERS[prompts.DEFAULT_PROMPT_KIND]


def test_get_prompt_builder_unknown_kind_raises():
    with pytest.raises(ValueError) as excinfo:
        prompts.get_prompt_builder("not-a-kind")
    # The error should name the valid kinds so CLI users can self-correct.
    for kind in EXPECTED_KINDS:
        assert kind in str(excinfo.value)


def test_generate_meeting_summary_prompt_dispatches_by_kind():
    rendered = prompts.generate_meeting_summary_prompt(
        markdown_notes=NOTES_SENTINEL, personal_info=INFO_SENTINEL, kind="realtor"
    )
    assert "Real Estate" in rendered
    assert NOTES_SENTINEL in rendered


def test_generate_meeting_summary_prompt_defaults_to_default_kind():
    via_default = prompts.generate_meeting_summary_prompt(
        markdown_notes=NOTES_SENTINEL, personal_info=INFO_SENTINEL
    )
    via_explicit = prompts.generate_meeting_summary_prompt(
        markdown_notes=NOTES_SENTINEL,
        personal_info=INFO_SENTINEL,
        kind=prompts.DEFAULT_PROMPT_KIND,
    )
    assert via_default == via_explicit


def test_generate_meeting_summary_prompt_unknown_kind_raises():
    with pytest.raises(ValueError):
        prompts.generate_meeting_summary_prompt(kind="not-a-kind")
