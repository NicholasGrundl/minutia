# Pytest Assertions Guide

## Core Concepts
Pytest uses standard Python `assert` statements but provides "assertion rewriting" to produce detailed failure reports with introspection.

### 1. Basic Assertions
```python
def test_function():
    assert f() == 4
# Failure shows: E assert 3 == 4 where 3 = f()
```

### 2. Floating Point Equality
Use `pytest.approx` to handle rounding errors.
```python
def test_floats():
    assert (0.1 + 0.2) == pytest.approx(0.3)
```

### 3. Expected Exceptions
Use `pytest.raises` as a context manager.
```python
def test_zero_division():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        1 / 0
```

### 4. Exception Groups (Python 3.11+)
Use `pytest.RaisesGroup` to verify multiple exceptions.
```python
def test_exception_in_group():
    with pytest.RaisesGroup(ValueError):
        raise ExceptionGroup("msg", [ValueError("foo")])
```

## Advanced Introspection
### `pytest_assertrepr_compare`
Implement this hook in `conftest.py` for custom object comparison output.

```python
def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, MyObj) and op == "==":
        return ["Comparing MyObj instances:", f"val: {left.val} != {right.val}"]
```

## Best Practices
- **One Behavior Per Test**: While a test can have multiple asserts, they should all relate to the same single behavior.
- **Avoid Boolean Returns**: Never do `return a == b`. Pytest ignores return values; always use `assert a == b`.
- **Use `match`**: When checking exceptions, always use the `match` parameter to verify the error message is what you expect, preventing false positives.
