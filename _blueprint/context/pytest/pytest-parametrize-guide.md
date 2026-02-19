# Pytest Parametrization Guide

## Core Concepts
Parametrization allows running a test function multiple times with different sets of arguments. This reduces redundancy and ensures broad coverage of input scenarios.

### 1. `@pytest.mark.parametrize`
The primary decorator for parametrizing test functions.

```python
import pytest

@pytest.mark.parametrize("test_input,expected", [
    ("3+5", 8),
    ("2+4", 6),
    pytest.param("6*9", 42, marks=pytest.mark.xfail)
])
def test_eval(test_input, expected):
    assert eval(test_input) == expected
```

### 2. Stacking Parametrize Decorators
Stacking creates a Cartesian product of all argument sets.

```python
@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("y", [2, 3])
def test_foo(x, y):
    # Runs 4 times: (0,2), (1,2), (0,3), (1,3)
    pass
```

### 3. `pytest_generate_tests` (Advanced)
Use this hook for dynamic parametrization based on command-line options or environment state.

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption("--stringinput", action="append", default=[])

def pytest_generate_tests(metafunc):
    if "stringinput" in metafunc.fixturenames:
        metafunc.parametrize("stringinput", metafunc.config.getoption("stringinput"))
```

## Best Practices
- **Use `pytest.param`**: Use it to add metadata like `xfail` or `skip` to specific test cases within a set.
- **Cartesian Products**: Be careful with stacked decorators; they can lead to an exponential explosion of test cases.
- **Test IDs**: Use the `ids` parameter to make test failure reports readable (e.g., `ids=["case_a", "case_b"]`).
