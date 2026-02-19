# Pytest Execution & Invocation Guide

## Core Concepts
Pytest offers flexible ways to discover and run tests, from full suite runs to targeting specific methods or parametrizations.

### 1. Targeted Execution
Run specific tests to save time and get faster feedback.

```bash
# By Module/Directory
pytest tests/test_api.py
pytest tests/unit/

# By Keyword Expression (-k)
pytest -k "MyClass and not test_method"

# By Precise Path (::)
pytest tests/test_mod.py::TestClass::test_method

# By Marker (-m)
pytest -m "slow"
```

### 2. Identifying Performance Bottlenecks
Use the `--durations` flag to find the slowest tests in your suite.

```bash
# Show the 10 slowest tests
pytest --durations=10
```

## Best Practices
- **Use Keyword Expressions (`-k`)**: This is the fastest way to run a subset of tests during active development without modifying code.
- **Categorize with Markers**: Use custom markers (e.g., `@pytest.mark.integration`) to separate fast unit tests from slow integration tests.
- **Fail Fast**: Use `pytest -x` to stop the test session after the first failure, which is ideal for debugging a single regression.
- **Max Failures**: Use `pytest --maxfail=2` to stop after a specific number of failures.
