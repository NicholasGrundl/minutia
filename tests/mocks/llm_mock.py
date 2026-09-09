from unittest.mock import MagicMock

import pytest


class LLMMock:
    """Simulates Anthropic Claude API behavior for testing."""

    def __init__(self):
        self.responses = []  # List of strings to return in sequence
        self.calls = []

    def set_responses(self, responses: list[str]):
        """Set a sequence of responses for the mock to return."""
        self.responses = responses

    def create_message(self, **kwargs):
        self.calls.append(kwargs)

        if not self.responses:
            text = "Default mocked summary."
        else:
            text = self.responses.pop(0)

        # Mimic the Anthropic SDK response structure: response.content[0].text
        # Using MagicMock to simulate the Pydantic models in the real SDK.
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = text
        mock_content.type = "text"
        mock_response.content = [mock_content]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_response.model = kwargs.get("model", "claude-3-5-sonnet-20240620")
        mock_response.id = "msg_mock_123"
        return mock_response


@pytest.fixture
def mock_llm(mocker, chaos_config):
    """
    Mock the Anthropic client and configuration globally.
    """
    mock_app_config = MagicMock()
    mock_app_config.anthropic_api_key = "fake-api-key"
    mock_app_config.base_output_dir = "runs"
    mock_app_config.log_level = "INFO"
    mock_app_config.mic_track = 3
    mock_app_config.desktop_track = 2
    mock_app_config.whisper_model = "base"
    mock_app_config.summary_model = "claude-sonnet-4-6"
    mock_app_config.recordings_dir = None
    mock_app_config.personal_info_path = None

    mock_resolution = MagicMock()
    mock_resolution.settings = mock_app_config
    mocker.patch("minutia.config.resolve_settings", return_value=mock_resolution)
    mocker.patch(
        "minutia.baseline_pipeline.resolve_settings", return_value=mock_resolution
    )
    mocker.patch("minutia.cli.app.resolve_settings", return_value=mock_resolution)

    mock_inst = LLMMock()

    def mock_create_message(**kwargs):
        chaos_config.trigger_if_set("anthropic.messages.create")
        return mock_inst.create_message(**kwargs)

    # Mock Anthropic client instantiation
    def mock_anthropic_init(api_key=None, **kwargs):
        chaos_config.trigger_if_set("anthropic.init")
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = mock_create_message
        return mock_client

    # Patch Anthropic class where it is used
    mocker.patch(
        "minutia.steps.summarize_transcript.Anthropic", side_effect=mock_anthropic_init
    )

    return mock_inst
