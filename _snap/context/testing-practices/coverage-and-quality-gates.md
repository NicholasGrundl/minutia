# Coverage and Quality Gates

## Use coverage diagnostically

Statement coverage answers whether a line executed. Branch coverage also checks whether the
possible destinations from conditional control flow were taken. Neither proves that an
assertion would detect an incorrect result.

Use coverage to find questions:

- Which behavior has no test at all?
- Which error or fallback branch never executes?
- Is a module covered only incidentally through a broad end-to-end test?
- Which tests cover a line that is about to change?
- Does subprocess execution contribute to the measurement as expected?

Per-test coverage contexts (`--cov-context=test`) can connect executed lines to pytest node IDs
and phases. This is useful for finding duplicated broad coverage or identifying the smallest
tests that protect a refactor.

## Threshold policy

A single global percentage is easy to game. A stronger policy combines:

- A modest repository floor that prevents large regression.
- Branch coverage.
- High expectations for new or changed deterministic core logic.
- Explicit exclusions for generated code or intentionally unreachable defensive paths.
- Review of uncovered lines rather than blind pursuit of 100 percent.

Do not add trivial tests merely to execute getters, imports, or constants. Delete unreachable
code when that is the honest conclusion.

## Subprocess coverage is version-sensitive

Recent pytest-cov documentation states that pytest-cov 7 removed its earlier subprocess support
and delegates to Coverage.py's subprocess patch configuration. Always consult the documentation
matching the locked versions before changing coverage configuration. Also verify coverage in a
small known subprocess case rather than assuming configuration works.

## Warnings

Warnings often predict future dependency or platform breakage. A useful policy is:

- Fail on unexpected warnings in controlled project code.
- Assert expected warnings with `pytest.warns` and a meaningful match.
- Scope filters narrowly to a warning class, module, and reason.
- Track third-party warning filters and remove them when dependencies are upgraded.

Avoid a blanket ignore filter. It turns a diagnostic channel into silence.

## Pytest strictness

Register markers and enable strict behavior supported by the installed pytest version. Pytest
9 added unified `strict = true`; older supported versions need individual options such as
strict marker and strict config handling. Version-match this configuration.

Strict expected failures are valuable: an unexpected pass should force a decision to remove or
update the `xfail` rather than silently persisting stale metadata.

## Mutation testing

Mutation testing changes production expressions and checks whether tests fail. It can reveal
weak assertions behind high coverage, but is computationally expensive and sensitive to slow
tests. Consider it only after the fast deterministic suite is healthy. Start with one important
pure module, not the whole pipeline.

No mutation-testing tool is recommended by this context pack yet. Select and document one only
after checking maintenance, Python compatibility, configuration, and incremental execution.

## Feedback loops

Maintain distinct commands for different needs:

- Very fast local selection for the code under change.
- Full unit suite.
- Unit plus hermetic integration suite.
- Coverage job.
- Slow or live smoke suite, opt-in and separately authorized.

Report slowest tests periodically. Optimize expensive setup only after measuring it; a broad
fixture scope that saves time can introduce shared-state failures that cost much more.

## References

- [Coverage.py branch coverage](https://coverage.readthedocs.io/en/latest/branch.html)
- [Coverage.py contexts](https://coverage.readthedocs.io/en/latest/contexts.html)
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/stable/config.html)
- [pytest-cov contexts](https://pytest-cov.readthedocs.io/en/latest/contexts.html)
- [pytest-cov subprocess support](https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html)
- [Pytest warning capture](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
- [Pytest good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

