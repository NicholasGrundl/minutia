import pytest

class LLMMock:
    """Simulates Anthropic Claude API behavior for testing."""
    
    def __init__(self):
        self.responses = [] # List of strings to return in sequence
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
            
        # Mock the Anthropic response structure: response.content[0].text
        class Content:
            def __init__(self, text):
                self.text = text
        
        class Response:
            def __init__(self, text):
                self.content = [Content(text)]
                
        return Response(text)

from tests.mocks.chaos_config import chaos_config

@pytest.fixture
def mock_llm(mocker, chaos_config):
    """
    Mock the Anthropic client in summarize_transcript.
    """
    from minutia.steps import summarize_transcript
    
    mock_inst = LLMMock()
    
    def mock_create_message(**kwargs):
        chaos_config.trigger_if_set("anthropic.messages.create")
        return mock_inst.create_message(**kwargs)

    # We need to mock the Anthropic CLASS so when it's instantiated it returns our mock client
    def mock_anthropic_init(api_key=None):
        chaos_config.trigger_if_set("anthropic.init")
        mock_client = mocker.Mock()
        mock_client.messages.create.side_effect = mock_create_message
        return mock_client
    
    mocker.patch.object(summarize_transcript, "Anthropic", side_effect=mock_anthropic_init)
    
    # Also mock API key resolution to avoid needing a real key in tests
    mocker.patch.object(summarize_transcript, "resolve_anthropic_api_key", return_value="fake-api-key")
    
    return mock_inst
