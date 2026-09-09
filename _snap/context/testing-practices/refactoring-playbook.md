# Test-Suite Refactoring Playbook

This is a behavior-preserving workflow. It is intentionally separate from any specific current
suite structure.

## 1. Establish the baseline

Before editing tests, record:

- Python, pytest, and plugin versions.
- Collection count and marker distribution.
- Full-suite result.
- Unit and integration results separately.
- Slowest tests.
- Unexpected warnings.
- Statement and branch coverage.
- Known flaky or environment-dependent cases.

Save exact commands and output summaries. A refactor cannot be evaluated without a before state.

## 2. Inventory behaviors, not files

Map public behaviors and important risks to their existing protection:

```text
Behavior or risk -> test boundary -> scenario -> confidence gap
```

Look for duplicated coverage, behaviors protected only by end-to-end tests, and tests that assert
implementation details without proving an outcome.

## 3. Characterize fragile boundaries

Before moving fixtures or changing mocks, add minimal characterization around behavior that is
currently trusted but hard to observe. Use small reviewed golden artifacts where a complete
serialized result is the meaningful contract.

Do not “improve” product behavior during this phase. Record suspected defects separately.

## 4. Define the project testing policy

Complete [policy-template.md](policy-template.md). In particular, settle:

- Tier definitions and time budgets.
- Network and credential rules.
- Fixture and autouse rules.
- Mock/fake/contract strategy.
- Golden-update process.
- Skip and `xfail` ownership.
- Coverage and warning gates.
- Parallel-safety expectations.

## 5. Refactor in narrow slices

Useful slice order:

1. Make test names and markers honest.
2. Extract plain builders/helpers from fixtures that need no pytest lifecycle.
3. Replace mutable broad-scope fixtures with fresh function-scope scenario data.
4. Introduce factory fixtures where many near-duplicate fixtures exist.
5. Replace permissive mocks with autospecced boundaries or small fakes.
6. Replace direct `unittest.mock` imports with pytest-mock's `mocker` unless a documented edge
   case requires the stdlib interface directly.
7. Add contract tests for important fakes and external adapters.
8. Consolidate duplicated golden data only when ownership remains obvious.
9. Improve assertions and failure messages.
10. Enable stricter markers, config, warnings, and expected failures incrementally.

Run the smallest affected selection after each slice, then the relevant tier. Keep production
changes separate when practical so test-structure failures remain diagnosable.

## 6. Prove isolation

After the suite is structurally clearer:

- Run representative tests alone.
- Run modules in different orders.
- Repeat suspected stateful tests.
- Run without user credentials and config.
- Run from a clean temporary environment where feasible.
- Try xdist only after sequential determinism is established.

Parallel failures are evidence of shared state until shown otherwise.

## 7. Evaluate effectiveness

Compare before and after:

- Same intended behaviors protected.
- Reduced default-suite runtime or no unjustified regression.
- Fewer hidden fixture dependencies.
- Clearer failure diagnostics.
- No unexpected network or filesystem access.
- Branch gaps are understood.
- Tests survive internal refactoring without losing behavioral protection.

The success measure is confidence and maintainability, not fewer lines or a higher raw test
count.

## Review questions

- Can a reader understand the scenario from the test and its direct inputs?
- If the implementation were wrong in a plausible way, would the assertion fail?
- Does this test live at the narrowest useful boundary?
- Is every double consistent with a real contract?
- Can this test run alone and in parallel safely?
- Does failure output say what behavior broke?
- Is the test more stable than the implementation detail it protects?
