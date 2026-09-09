# Regression, Characterization, and Property Testing

## Characterize before structural refactoring

When behavior is trusted but poorly covered, add tests at stable observable boundaries before
moving helpers or reorganizing fixtures. A characterization test records what the system does
today. It does not claim every current behavior is desirable.

For each characterized behavior, label one of these intentions in the test name or review:

- Contract: must remain stable.
- Compatibility: retained temporarily for callers or existing artifacts.
- Suspected defect: captured only to make an intentional later change visible.

This distinction prevents golden files from accidentally canonizing a bug forever.

## Golden files and snapshots

Golden tests are useful when a result is naturally a structured artifact and reviewing the
whole artifact is easier than maintaining many individual assertions. Good candidates include
normalized JSON, Markdown reports, serialized metadata, and deterministic command plans.

Before comparison, normalize only non-contractual variability:

- Temporary root paths.
- Generated IDs.
- Wall-clock timestamps.
- Platform-specific path separators or line endings when cross-platform identity is intended.
- Provider metadata explicitly outside the application's contract.

Do not normalize away ordering, fields, whitespace, or numeric values that users depend on.
Normalization code is production-adjacent test logic and needs focused tests of its own.

Golden-file policy should require:

- Expected artifacts are committed and human-readable where possible.
- Missing expectations fail; they do not silently auto-create a passing result.
- Updates require an explicit command or flag.
- Reviewers inspect the semantic diff.
- Bulk updates are explained rather than accepted mechanically.
- Generation provenance and normalization steps are documented.

`pytest-regressions` is well suited to external YAML/text files and numeric or image
comparisons. Syrupy provides idiomatic pytest snapshots colocated with tests. Evaluate diff
quality, serialization control, compatibility, and update ergonomics before choosing either.

## Property-based tests

Example-based tests demonstrate known scenarios. Property-based tests explore many inputs that
share an invariant and shrink a failure toward a small reproducer.

Good properties for transformation pipelines include:

- Output ordering is monotonic under a defined key.
- Every valid input item appears exactly once after a merge.
- Adding an empty input is an identity operation.
- Serialization followed by deserialization preserves the defined model.
- Normalization is idempotent.
- A forced overwrite changes only allowed outputs.
- Invalid time intervals or schemas are rejected consistently.

Avoid weak properties such as “the result is not `None`” or restating the implementation in the
test. Prefer an independent oracle, algebraic law, or domain invariant.

## Hypothesis practices

- Begin with simple strategies composed from primitives.
- Generate valid domain objects by construction rather than filtering heavily.
- Use `@example` for known regressions that must remain prominent.
- Let Hypothesis manage seeds and its example database; do not add ad hoc randomness.
- Keep generated tests deterministic with respect to the drawn input.
- Use profiles to separate a quick local budget from a stronger CI budget.
- Add `note()` or meaningful representations when failure output needs domain context.
- Use stateful testing only for genuinely sequential APIs with meaningful operation sequences.

A Hypothesis test can use pytest fixtures, but function-scoped fixture state is not reset for
each generated example. Mutable fixture state therefore needs particular care.

## Metamorphic tests

When exact expected output is expensive or impossible to specify, check relationships between
runs. Examples:

- Reordering independent input files does not change a chronology-based merged result.
- Shifting every timestamp by the same amount shifts output timestamps by that amount while
  preserving content and ordering.
- Running a deterministic stage twice produces byte-identical output.

Metamorphic tests are especially useful around algorithms and media metadata, but they should
not be used to test inherently nondeterministic language-model prose.

## AI-generated output

Do not snapshot live model prose. It is nondeterministic and provider behavior can change. Test
separate concerns instead:

- Prompt/request construction with stable normalized expectations.
- Parsing and validation using representative controlled responses.
- Error translation and retries with a fake client.
- Filename and artifact rules using deterministic returned content.
- A manually invoked live smoke evaluation when explicitly authorized and budgeted.

## References

- [Hypothesis tutorial](https://hypothesis.readthedocs.io/en/latest/tutorial/)
- [Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html)
- [Hypothesis pytest integration](https://hypothesis.readthedocs.io/en/latest/reference/integrations.html)
- [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html)
- [pytest-regressions](https://pytest-regressions.readthedocs.io/en/latest/)
- [Syrupy](https://syrupy-project.github.io/syrupy/)

