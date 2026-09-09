# Fixtures and Test Data

## Fixtures are a dependency graph

Pytest resolves fixture names from test parameters, runs their dependencies, caches one result
per applicable fixture instance, and tears yield fixtures down in reverse order. This is
powerful, but a large fixture graph hides setup and can make a test hard to understand.

Use a fixture when pytest should manage at least one of these concerns:

- Lifecycle or cleanup.
- Scope and sharing.
- Parametrization.
- Access to another pytest fixture.
- Registration as part of the test environment.

Use a plain helper, builder, dataclass, or factory when none of those applies. Plain Python is
easier to call directly, type, compose, and understand.

## Default to function scope

Function scope provides the strongest isolation. Broader scopes trade isolation for setup
speed and should be justified by an expensive immutable resource.

- `function`: default for mutable data, patches, temporary workspaces, and most collaborators.
- `module` or `package`: occasionally useful for expensive read-only artifacts.
- `session`: suitable for immutable source data or a costly shared service only when state is
  reset per test.

Remember that a session-scoped fixture is once per xdist worker, not necessarily once per
entire distributed run. Parametrized fixtures may also execute more than once inside their
declared scope because pytest caches one instance per parameter at a time.

## Keep fixtures atomic

A fixture that performs several state-changing setup operations can fail halfway through and
leave partial state. Prefer one reversible action per fixture, with cleanup paired directly
after its `yield`. Compose those fixtures through dependencies.

```python
@pytest.fixture
def workspace(tmp_path):
    path = tmp_path / "workspace"
    path.mkdir()
    yield path
    # tmp_path owns removal; only add cleanup for external state created here.
```

Do not add cleanup merely for symmetry when the owning fixture already guarantees it.

## Prefer factory fixtures for scenario variation

A fixture that returns a factory lets the test show the values that matter:

```python
@pytest.fixture
def segment_factory():
    def make(*, start=0.0, end=1.0, text="hello", source="microphone"):
        return {
            "start": start,
            "end": end,
            "text": text,
            "source": source,
        }

    return make
```

This is often clearer than a family of nearly identical named fixtures. If the factory does not
need pytest resources, make it a normal helper instead.

## Control autouse fixtures

Autouse behavior is intentionally invisible at the test signature. Reserve it for suite-wide
guardrails, such as preventing accidental network access or clearing a dangerous global, where
invisibility is worth the tradeoff. Avoid autouse fixtures that create core scenario data or
change the happy-path behavior of every test.

## Parametrization

Parametrize data when multiple cases exercise the same behavior and assertion shape. Prefer
`pytest.param(..., id="meaningful-case")` for non-obvious values.

Good uses:

- Input partitions and boundary values.
- Equivalent supported formats.
- One behavior across multiple implementations.
- Error cases with the same expected error contract.

Split the test when cases require substantially different setup, actions, or assertions.
Avoid Cartesian products that create many cases without adding meaningful coverage. Parameter
objects are passed as-is rather than copied, so do not mutate a shared mutable parameter.

Use `pytest_generate_tests` only when ordinary parametrization cannot express the requirement.
Dynamic generation makes collection and debugging more complex and must be deterministic across
xdist workers.

## Files and directories

- Use `tmp_path` for a unique `pathlib.Path` per test.
- Use `tmp_path_factory` for an expensive immutable file shared at a broader fixture scope.
- Do not write to repository fixtures during normal test execution.
- Do not depend on the user's current directory, home directory, config files, or output paths.
- Specify encodings and newline behavior when those are part of the contract.
- Keep checked-in sample files small, realistic, reviewable, and free of secrets or personal
  information.

## Test-data ownership

Keep three concepts distinct:

- Builder/default data: convenient valid objects with explicit overrides.
- Scenario fixture: the state needed for one behavior.
- Golden artifact: a reviewed expected output whose full representation is contractual.

Store golden inputs and outputs together by scenario when that makes provenance obvious. Every
generated fixture should document how it was produced, what was normalized, and whether it can
be regenerated without paid services.

## References

- [How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [About fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [Temporary paths](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [pytest-xdist how-tos](https://pytest-xdist.readthedocs.io/en/stable/how-to.html)

