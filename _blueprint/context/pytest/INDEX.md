# Pytest Context Index

This directory contains a comprehensive, multi-layered guide to building and maintaining a world-class test suite with `pytest`. Use this index to find the specific patterns or architectural guidance you need.

## 1. Core Syntax & Foundations
- **[pytest-general-foundations.md](./pytest-general-foundations.md)**: Entry-level overview of test discovery, naming, and basic `assert`.
- **[pytest-assertions-guide.md](./pytest-assertions-guide.md)**: Deep dive into smart diffs, `pytest.approx` for floats, and `pytest.raises` for exception testing.

## 2. Dependency Injection (Fixtures)
- **[pytest-fixtures-guide.md](./pytest-fixtures-guide.md)**: Procedural guide to implementing fixtures, scopes (`function` to `session`), `yield` teardowns, and factories.
- **[pytest-fixture-philosophy.md](./pytest-fixture-philosophy.md)**: Architectural "Why" behind fixtures, focusing on explicit dependencies and composability over xUnit-style setup/teardown.

## 3. Data-Driven Testing
- **[pytest-parametrize-guide.md](./pytest-parametrize-guide.md)**: Patterns for `@pytest.mark.parametrize`, Cartesian products (stacking), and `pytest.param` metadata.

## 4. Isolation & Mocking
- **[pytest-monkeypatch-guide.md](./pytest-monkeypatch-guide.md)**: Best practices for using the `monkeypatch` fixture to isolate system state, environment variables, and external APIs.

## 5. Architecture & Best Practices
- **[pytest-organization-guide.md](./pytest-organization-guide.md)**: Standard project layouts (`src` layout), `conftest.py` strategies, and `importlib` import modes.
- **[pytest-expert-practices.md](./pytest-expert-practices.md)**: Advanced guidance on long-term maintenance, `tox` integration, and the benefits of "Strict Mode."
- **[pytest-project-guidance.md](./pytest-project-guidance.md)**: Local, project-specific testing rules and conventions.

## 6. Execution & Specialized Tools
- **[pytest-execution-guide.md](./pytest-execution-guide.md)**: CLI patterns for targeted runs (`-k`, `-m`, `::`), performance profiling (`--durations`), and "fail-fast" flags.
- **[pytest-temp-logging-guide.md](./pytest-temp-logging-guide.md)**: How to use `tmp_path` (modern `pathlib`) and `caplog` for system-level assertions.
- **[pytest-skipping-guide.md](./pytest-skipping-guide.md)**: Managing known bugs with `xfail` and platform-specific tests with `skipif`.

## 7. External Sources
- **[RESOURCES.md](./RESOURCES.md)**: The original URLs and source mapping for this entire context set.
