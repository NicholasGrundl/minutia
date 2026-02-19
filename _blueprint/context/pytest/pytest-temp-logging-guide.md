# Pytest Temp Files & Logging Guide

## Temporary Files (`tmp_path`)
The `tmp_path` fixture provides a unique `pathlib.Path` directory for each test.

```python
def test_file_io(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    f = d / "test.txt"
    f.write_text("hello")
    assert f.read_text() == "hello"
```

### `tmp_path_factory` (Session Scoped)
Use this for sharing temporary data across multiple tests or for expensive setup.

```python
@pytest.fixture(scope="session")
def shared_data(tmp_path_factory):
    dir = tmp_path_factory.mktemp("data")
    # ... create expensive data ...
    return dir
```

## Logging (`caplog`)
Pytest captures logs of level WARNING or above by default.

### 1. Asserting on Logs
```python
def test_log_output(caplog):
    caplog.set_level(logging.INFO)
    some_action_that_logs()
    
    assert "Expected message" in caplog.text
    for record in caplog.records:
        assert record.levelname != "ERROR"
```

### 2. Live Logs (CLI)
View logs as they happen during a test run:
`pytest --log-cli-level=INFO`

## Best Practices
- **Avoid `tmpdir`**: `tmp_path` is the modern `pathlib` based version and should be preferred over the legacy `py.path.local` `tmpdir`.
- **Log Levels**: Use `caplog.at_level` context manager to temporarily boost log levels for specific assertions without affecting the rest of the test suite.
- **Clean up**: Pytest automatically keeps the last 3 `tmp_path` directories for debugging; you don't need to manually delete them.
