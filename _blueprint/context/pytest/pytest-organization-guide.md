# Pytest Project Organization Guide

## Core Concepts
Following standard layouts ensures `pytest` can discover tests efficiently and avoids import headaches.

### 1. Recommended Layout (src layout)
Keep application code in `src/` and tests in `tests/`.

```text
pyproject.toml
src/
  mypkg/
    __init__.py
    app.py
tests/
  test_app.py
  conftest.py
```

### 2. Configuration (`pyproject.toml`)
Enable `importlib` mode to avoid naming conflicts and improve reliability.

```toml
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
testpaths = ["tests"]
pythonpath = ["src"]
```

### 3. Test Discovery Rules
- Files: `test_*.py` or `*_test.py`.
- Classes: `Test*` (without `__init__`).
- Functions/Methods: `test_*`.

## Best Practices
- **Editable Installs**: Always use `pip install -e .` during development so your tests run against the code you are currently editing.
- **`conftest.py` Strategy**:
    - Root `conftest.py`: Global fixtures and hooks.
    - Sub-directory `conftest.py`: Fixtures specific to a module or feature set.
- **Strict Mode**: Use `strict = true` in your config to ensure markers are registered and to prevent accidental "pass" results on empty test sets.
