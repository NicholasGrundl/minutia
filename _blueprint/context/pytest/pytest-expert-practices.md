# Pytest Expert Practices & Long-Term Maintenance

## Core Philosophy
Modern pytest projects should prioritize **predictability**, **isolation**, and **scalability**. The following practices ensure that a test suite remains a high-signal tool rather than a maintenance burden as it grows.

### 1. The `src` Layout vs. `root` Layout
Pytest strongly recommends the **`src` layout** for all new projects.

**Why?**
- **Import Integrity**: It forces you to install your package (usually in editable mode with `pip install -e .`) to run tests. This ensures that the code you are testing is the same code that an end-user would import, preventing "import-from-current-dir" false positives.
- **Clean Namespace**: It keeps your project root clean of application sub-packages, making it easier for tools like `tox` and `coverage` to distinguish between your code and its tests.

### 2. Import Modes: `importlib` (Modern) vs. `prepend` (Legacy)
You should explicitly set `addopts = ["--import-mode=importlib"]` in your configuration.

**Why?**
- **Uniqueness**: The legacy `prepend` mode adds each test directory to `sys.path`, which requires all test filenames to be globally unique across the entire project.
- **Reliability**: `importlib` doesn't change `sys.path`, which avoids many subtle import bugs and allows you to have `test_utils.py` in multiple subdirectories without collision.

### 3. Integrated Build Tools (`tox`)
Use `tox` for local and CI test automation across different Python versions.

**Why?**
- **Isolation**: `tox` creates a fresh virtualenv for each run and installs your package from its source distribution. This catches missing dependencies or packaging errors that would be invisible if you only ran `pytest` in your development environment.

### 4. Strict Mode and Linting
Enable strict mode by setting `strict = true` in your configuration.

**Why?**
- **Marker Safety**: It prevents silent failures due to misspelled markers (e.g., `@pytest.mark.solw` instead of `slow`).
- **Enforced Standards**: Use `flake8-pytest-style` to automatically check for anti-patterns like using `unittest.TestCase` or incorrect fixture naming.

### 5. Config File Strategy
Prefer `pyproject.toml` for all pytest configuration.

**Why?**
- **Single Source of Truth**: Modern Python tooling is consolidating on `pyproject.toml`. Keeping your `testpaths`, `pythonpath`, and `addopts` here ensures consistency across all tools in your stack.
