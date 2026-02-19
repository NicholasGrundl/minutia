# Pytest Skip & Xfail Guide

## Core Concepts
Manage tests that cannot succeed under certain conditions without failing the entire suite.

### 1. Skipping Tests
Use `skip` for tests that should not run at all.

```python
# Unconditional skip
@pytest.mark.skip(reason="Feature not implemented")

# Conditional skip (Platform/Version specific)
@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")

# Imperative skip (Runtime check)
def test_resource():
    if not resource_available():
        pytest.skip("Resource not found")
```

### 2. Expected Failures (Xfail)
Use `xfail` for known bugs or features under development. The test still runs, but its failure won't "break" the build.

```python
@pytest.mark.xfail(reason="Known bug #123", strict=True)
def test_buggy_feature():
    assert buggy_code() == True
```

## Best Practices
- **`strict=True`**: Always use `strict=True` for `xfail`. This ensures that if the test unexpectedly passes (`XPASS`), it will be reported as a **FAILURE**. This prevents bugs from being "fixed" silently without you knowing.
- **`raises` parameter**: Use `raises=IndexError` with `xfail` to ensure the test only "passes" its failure if it fails for the specific reason you expect.
- **`importorskip`**: Use `pytest.importorskip("my_module")` at the module level to skip all tests if an optional dependency is missing.
