# Suite Architecture

## Start from risks and boundaries

A test tier should describe what the test crosses and how quickly it can provide reliable
feedback. File location and marker names should follow that definition, not create it.

Useful boundaries for a Python pipeline application include:

- Pure transformations and validation.
- A use-case or orchestration API with controlled collaborators.
- Filesystem serialization and real local command execution.
- External SDK request/response contracts.
- Heavy local models or real remote services.
- The installed CLI as a user invokes it.

Put most cases at the narrowest boundary that can observe the behavior. Keep a smaller number
of tests across adjacent boundaries, and a very small number across the entire system. This is
the practical value of a test pyramid: faster feedback and clearer fault localization, not a
prescribed percentage.

## Suggested test tiers

### Unit

A unit test should normally have all of these properties:

- Runs in process.
- Uses no network, subprocess, GPU, large model, or user filesystem.
- Uses only an isolated `tmp_path` when filesystem behavior is itself under test.
- Controls clock, randomness, environment, and machine-specific values.
- Produces the same result alone, after another test, or in a different order.
- Usually completes in milliseconds.

The unit does not have to be a single function. Testing a coherent use case through its stable
public entry point is often less coupled than testing every private helper.

### Integration

An integration test proves that two or more real components agree. Examples include:

- A serializer writes a real file and the corresponding loader reads it.
- A wrapper builds arguments that a real local executable accepts.
- Configuration layers resolve correctly from a controlled environment and directory.
- An SDK adapter converts a representative response into the application's own model.

Integration tests may use local files and subprocesses, but should still be hermetic: no user
configuration, no uncontrolled network, and no shared output paths.

### Contract

A contract test verifies the assumptions at one boundary without requiring the whole pipeline.
It should cover the smallest payloads necessary to detect a mismatch:

- Outbound argument or request shape.
- Required response fields and types.
- Error translation.
- Version or capability probing.

Run the same contract against a fake and the real local implementation when practical. For a
remote paid API, validate representative SDK-shaped responses in normal CI and reserve real
calls for an explicitly authorized smoke job.

### Slow or end-to-end

These tests may load real models, process representative media, or exercise a complete user
workflow. They should have explicit markers, budgets, prerequisites, and ownership. They are
valuable because they catch wiring errors, but poor at exhaustively describing edge cases.

## Marker rules

- Register every custom marker so a misspelling cannot silently create a new category.
- Prefer a small stable vocabulary such as `unit`, `integration`, and `slow`.
- Define tiers by allowed resources and expected runtime in project policy.
- Avoid marking the same test as every tier. Choose its broadest real boundary.
- Treat `skip` as an environmental fact with a reason.
- Treat `xfail` as a tracked, temporary defect with a reason and preferably strict behavior.
- Do not use markers as a substitute for a clear directory and ownership structure.

## Assertions and observability

Assert outcomes meaningful to a caller:

- Returned data and durable artifacts.
- Exit code and appropriate output channel.
- A translated error type and useful message fragment.
- Calls at an external boundary when the call itself is the behavior.
- Absence of a forbidden side effect.

Avoid assertions that merely repeat implementation details:

- Exact private-helper call chains.
- Complete mock call order when order is not contractual.
- Incidental whitespace, paths, timestamps, IDs, or logger formatting.
- Type assertions already guaranteed by a stronger behavioral assertion.

One test may contain several related assertions when they describe one behavior. Give complex
comparisons a domain-specific assertion helper so failures explain the meaningful difference.

## Test names

Names should make the scenario and expected outcome visible:

```text
test_<behavior>_when_<condition>
test_<operation>_<expected_outcome>
```

Parametrized cases need stable, descriptive IDs. IDs become the interface for `-k`, CI failure
reports, coverage contexts, and reproduction commands.

## References

- [Pytest good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [Pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Google test sizes](https://testing.googleblog.com/2010/12/test-sizes.html)
- [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Cosmic Python: High Gear and Low Gear](https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear)

