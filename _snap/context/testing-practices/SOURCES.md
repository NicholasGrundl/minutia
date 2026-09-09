# Sources and Provenance

Reviewed 2026-09-08. These are links and focused reading routes, not copied upstream manuals.
Prefer official documentation for API behavior. The design essays supplement the API docs and
are identified separately.

## Pytest core — primary sources

- [Pytest documentation](https://docs.pytest.org/en/stable/)
  - Canonical entry point for the installed pytest major/minor version.
- [Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
  - Test layout, import behavior, installed-package testing, and strict configuration.
- [How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
  - Fixture composition, scopes, factories, parametrization, yield cleanup, and safe teardown.
- [About fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
  - Conceptual model and fixture execution ordering.
- [Parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html)
  - Function and fixture parameters, IDs, per-case marks, and generated cases.
- [Temporary paths](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
  - `tmp_path`, `tmp_path_factory`, retention, and migration away from legacy `tmpdir`.
- [Monkeypatching](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
  - Safe changes to attributes, mappings, environment variables, working directory, and import
    paths. The docs recommend patching the reference used by the code and making controlled
    dependencies explicit where possible.
- [Markers](https://docs.pytest.org/en/stable/how-to/mark.html)
  - Registration, selection, skip, and expected-failure mechanics.
- [Logging](https://docs.pytest.org/en/stable/how-to/logging.html)
  - `caplog`, log levels, CLI output, and configuration.
- [Warning capture](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
  - `pytest.warns`, warning filters, and warning summaries.
- [Import mechanisms](https://docs.pytest.org/en/stable/explanation/pythonpath.html)
  - `prepend`, `append`, and `importlib` modes plus the difference between `pytest` and
    `python -m pytest`.
- [Flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html)
  - Shared state, order dependence, thread-safety cautions, diagnosis, and quarantine risks.
- [API reference](https://docs.pytest.org/en/stable/reference/reference.html)
  - Exact public API for fixtures, marks, assertions, warnings, hooks, and configuration.
- [Complete current PDF](https://media.readthedocs.org/pdf/pytest/latest/pytest.pdf)
  - Searchable offline archive. At review time, the PDF identified itself as pytest 9.2. Do not
    use the latest PDF for version-sensitive work when the project pins an older pytest.

## Pytest-native mocking — primary sources

Project preference: use pytest-mock's `mocker` fixture rather than importing mock classes or
patch helpers directly from `unittest.mock`. Use `monkeypatch` for environment and process
state. The standard-library documentation remains listed because pytest-mock intentionally
wraps that API and relies on its semantics.

- [pytest-mock documentation](https://pytest-mock.readthedocs.io/en/latest/)
  - The `mocker` fixture and automatic restoration.
- [pytest-mock usage](https://pytest-mock.readthedocs.io/en/latest/usage.html)
  - Patch, spy, stub, async stub, scoped mocker fixtures, and improved assertion output.
- [Pytest monkeypatching](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
  - Preferred for environment variables, dictionaries, attributes, paths, and working
    directory.
- [Python 3.12 `unittest.mock`](https://docs.python.org/3.12/library/unittest.mock.html)
  - Underlying API reference only. Read where to patch, autospeccing, `spec_set`, `side_effect`,
    call objects, async mocks, and partial mocking; normally access them through `mocker`.

## Coverage — primary sources

- [Coverage.py branch coverage](https://coverage.readthedocs.io/en/latest/branch.html)
  - Measures alternate control-flow destinations in addition to executed statements.
- [Coverage.py measurement contexts](https://coverage.readthedocs.io/en/latest/contexts.html)
  - Associates execution with named contexts.
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/en/latest/)
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/stable/config.html)
- [pytest-cov contexts](https://pytest-cov.readthedocs.io/en/latest/contexts.html)
  - `--cov-context=test` records the pytest node ID and setup/run/teardown phase.
- [pytest-cov subprocess support](https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html)
  - Version-sensitive: pytest-cov 7 removed its former subprocess mechanism in favor of
    Coverage.py's subprocess patch support.

## Property and regression testing — project documentation

- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/)
- [Hypothesis tutorial](https://hypothesis.readthedocs.io/en/latest/tutorial/)
- [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html)
- [Hypothesis pytest integration](https://hypothesis.readthedocs.io/en/latest/reference/integrations.html)
- [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html)
- [pytest-regressions](https://pytest-regressions.readthedocs.io/en/latest/)
  - Fixtures for structured data, text files, numeric values, arrays, and images.
- [Syrupy](https://syrupy-project.github.io/syrupy/)
  - Pytest snapshot plugin with explicit snapshot-update behavior.

These are candidate tools, not default dependencies. Select one only after identifying a real
gap in the existing suite.

## Parallel execution — primary sources

- [pytest-xdist documentation](https://pytest-xdist.readthedocs.io/en/stable/)
- [Distribution modes](https://pytest-xdist.readthedocs.io/en/stable/distribution.html)
- [How-tos](https://pytest-xdist.readthedocs.io/en/stable/how-to.html)
  - Worker identity, run identity, per-worker resources, and the fact that session fixtures run
    once in each worker rather than once globally.
- [Known limitations](https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html)
  - Consistent collection order, output capture, and debugger limitations.

## CLI testing — primary sources

- [Typer testing](https://typer.tiangolo.com/tutorial/testing/)
  - `CliRunner`, invocation, arguments, exit codes, stdout, and stderr.
- [Click testing](https://click.palletsprojects.com/en/stable/testing/)
  - Underlying runner behavior, temporary filesystem isolation, environment, and terminal
    dimensions. The current 8.5 documentation deprecates `CliRunner.isolated_filesystem()` and
    recommends `tmp_path` with absolute paths.

## Design guidance — supplemental sources

- [Google Testing Blog: Test Sizes](https://testing.googleblog.com/2010/12/test-sizes.html)
  - Classifies tests using observable resource constraints such as network, filesystem,
    subprocesses, and runtime rather than ambiguous names alone.
- [Software Engineering at Google: Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html)
  - Tradeoffs among test doubles and the design pressure created by code that is hard to fake.
- [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
  - A balanced test portfolio, contract tests, end-to-end tests, and avoiding duplication.
- [Architecture Patterns with Python: High Gear and Low Gear](https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear)
  - Testing at stable service boundaries with many fast use-case tests and fewer end-to-end
    tests.
- [Architecture Patterns with Python: Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository)
  - Fakes as design feedback and separating core behavior from infrastructure.

## Refresh procedure

When pytest or an important plugin is upgraded:

1. Record old and new versions.
2. Open the version-specific changelog and migration guidance.
3. Recheck only the affected context documents.
4. Update the review date and any version-qualified guidance here.
5. Keep project policy separate from upstream behavior so an upgrade does not silently change
   local expectations.
