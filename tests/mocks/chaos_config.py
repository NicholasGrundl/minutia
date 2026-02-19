import pytest

class ChaosConfig:
    """Manages error injection for mocks."""
    
    def __init__(self):
        self.failures = {} # mock_name -> exception_to_raise

    def set_failure(self, mock_name: str, exception: Exception):
        """Set an exception to be raised when mock_name is called."""
        self.failures[mock_name] = exception

    def clear_failures(self):
        self.failures = {}

    def trigger_if_set(self, mock_name: str):
        """Raise the configured exception if one is set for mock_name."""
        if mock_name in self.failures:
            exc = self.failures[mock_name]
            # Optionally remove after trigger if we want one-shot failures
            # del self.failures[mock_name]
            raise exc

@pytest.fixture
def chaos_config():
    """Fixture to manage error injection across mocks."""
    config = ChaosConfig()
    yield config
    config.clear_failures()
