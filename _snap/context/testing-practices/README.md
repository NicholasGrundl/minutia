# Testing Practices Context Pack

Curated, LLM-friendly guidance for designing and refactoring a capable Python test suite.
This topic is about testing strategy and reusable patterns; it is not a snapshot of Minutia's
current tests.

The source material was reviewed on 2026-09-08. Most links use a documentation site's
`stable` or `latest` route, which can change. Before applying version-specific configuration
or APIs, compare the installed dependency version with [SOURCES.md](SOURCES.md) and open the
matching version of the upstream documentation.

## Read this topic progressively

Do not load every file by default. Start here, then open the document matching the decision at
hand:

- [suite-architecture.md](suite-architecture.md) — boundaries, test tiers, markers, and where
  behavior should be tested.
- [fixtures-and-data.md](fixtures-and-data.md) — fixture scope, factories, parametrization,
  temporary files, and test-data ownership.
- [test-doubles.md](test-doubles.md) — mocks, stubs, spies, fakes, monkeypatching, and contract
  checks.
- [regression-and-property-testing.md](regression-and-property-testing.md) — golden files,
  snapshots, characterization tests, invariants, and Hypothesis.
- [determinism-and-parallelism.md](determinism-and-parallelism.md) — isolation, flaky-test
  prevention, ordering, clocks, randomness, and xdist constraints.
- [coverage-and-quality-gates.md](coverage-and-quality-gates.md) — meaningful coverage,
  warnings, strictness, mutation testing, and CI feedback loops.
- [cli-and-pipeline-testing.md](cli-and-pipeline-testing.md) — testing a CLI that coordinates
  filesystem, subprocess, model, and external-service boundaries.
- [refactoring-playbook.md](refactoring-playbook.md) — a behavior-preserving sequence for
  restructuring an existing suite.
- [policy-template.md](policy-template.md) — fill-in template for decisions that should be
  explicit in the repository.
- [SOURCES.md](SOURCES.md) — upstream sources, versions, and why each source matters.

## Working principles

1. Optimize for trustworthy feedback: deterministic failures, useful diagnostics, and short
   feedback loops.
2. Test observable behavior at the narrowest stable boundary that gives confidence.
3. Keep dependency setup visible. A large fixture graph is an implicit program and should be
   treated with the same care as production code.
4. Use real pure objects and value types. Replace expensive, nondeterministic, destructive, or
   externally owned boundaries with an appropriate test double.
5. Keep a small number of integration and end-to-end tests to prove that doubles agree with
   reality.
6. Treat test data, golden files, fixtures, helper functions, and plugins as maintained code.
7. Coverage is evidence about execution, not proof of correct assertions.
8. Never make a flaky test invisible with unconditional retries or a permanent non-strict
   `xfail`.
9. Stay within the pytest ecosystem by default: use pytest fixtures and assertions, prefer
   `monkeypatch` for environment/process state, and prefer pytest-mock's `mocker` fixture over
   direct imports from `unittest.mock`.

## Pytest-native preference

New and refactored tests should use pytest idioms consistently:

- Plain `assert`, `pytest.raises`, `pytest.warns`, and `pytest.approx`.
- Pytest fixtures and yield teardown instead of `unittest.TestCase` setup methods.
- `tmp_path` and `tmp_path_factory` instead of `tempfile` or legacy `tmpdir` APIs.
- `monkeypatch` for environment variables, mappings, attributes, paths, and working directory.
- pytest-mock's `mocker` fixture for mocks, call assertions, autospeccing, spies, and stubs.

Avoid direct `unittest.mock` imports in ordinary tests. Pytest-mock deliberately exposes the
same underlying mock API, so Python's `unittest.mock` documentation remains an important API
reference; keeping that reference does not make direct use the project default. Use a direct
stdlib mock only when pytest-mock cannot express a documented requirement cleanly.

## Version capture

Before a refactor, record tool versions without changing the suite:

```bash
uv run pytest --version
uv tree | rg 'pytest|coverage|hypothesis|typer'
```

Store the output with the refactor notes. In particular, do not copy current `strict = true`
examples into an older pytest configuration: unified strict mode was added in pytest 9.0.

## Suggested prompt for future agents

> Read `_snap/context/testing-practices/README.md`, then open only the linked context files
> relevant to the current testing decision. Treat `SOURCES.md` as provenance, not as a request
> to browse every source. Compare any version-sensitive recommendation with the locked package
> versions. Do not restructure production boundaries merely to satisfy a testing fashion;
> identify the behavior and risk first.
