# Pytest Monkeypatch & Mocking Guide

## Core Concepts
The `monkeypatch` fixture allows you to safely modify objects, dictionaries, or environment variables for the duration of a test. All changes are automatically undone after the test completes.

### 1. Patching Functions/Attributes
Use `monkeypatch.setattr` to replace a function or attribute with a mock.

```python
from pathlib import Path

def test_getssh(monkeypatch):
    def mock_home():
        return Path("/abc")
    
    monkeypatch.setattr(Path, "home", mock_home)
    assert Path.home() == Path("/abc")
```

### 2. Mocking API Responses (Requests)
A common pattern for isolating network calls.

```python
import requests

class MockResponse:
    @staticmethod
    def json():
        return {"key": "value"}

def test_api_call(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse()
    
    monkeypatch.setattr(requests, "get", mock_get)
    # Your code calling requests.get will now get MockResponse
```

### 3. Environment Variables
Safely test code that relies on `os.environ`.

```python
def test_env_logic(monkeypatch):
    monkeypatch.setenv("USER", "test_user")
    assert os.getenv("USER") == "test_user"
    
    monkeypatch.delenv("USER", raising=False)
    # Logic for missing env var
```

## Best Practices
- **`autouse` for Safety**: Use an `autouse` fixture in `conftest.py` to globally disable dangerous operations (like `requests.get`) to ensure tests never hit the real internet.
- **`monkeypatch.context()`**: Use this for fine-grained patching within a specific block of code inside a single test.
- **Prefer `monkeypatch` over `unittest.mock.patch`**: `monkeypatch` is more idiomatic in pytest and handles cleanup more reliably without decorators.
