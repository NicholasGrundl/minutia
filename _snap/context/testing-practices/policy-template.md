# Project Testing Policy Template

Copy the decided portions into the project's canonical testing documentation. Delete prompts
that do not apply; do not leave ambiguous placeholders masquerading as policy.

## Purpose

Our test suite exists to provide: `<fast local feedback, regression protection, interface
confidence, release evidence, ...>`.

## Test tiers

### Unit

- Allowed resources: `<...>`
- Forbidden resources: `<...>`
- Target per-test runtime: `<...>`
- Marker and location: `<...>`

### Integration

- Allowed resources: `<...>`
- Forbidden resources: `<...>`
- Target per-test runtime: `<...>`
- Marker and location: `<...>`

### Slow/end-to-end

- Prerequisites: `<...>`
- Credentials/cost policy: `<...>`
- Runtime ceiling: `<...>`
- Trigger and marker: `<...>`

### Contract

- Boundaries covered: `<...>`
- Fake-versus-real verification: `<...>`
- Live verification schedule: `<...>`

## Isolation

- Network default: `<blocked/allowed only for marked tests>`
- User config and credentials: `<...>`
- Filesystem policy: `<...>`
- Clock/randomness policy: `<...>`
- Shared mutable state policy: `<...>`
- Subprocess timeout and cleanup policy: `<...>`

## Fixtures and helpers

- Default fixture scope: `<function>`
- Broader-scope approval criteria: `<...>`
- Autouse uses permitted: `<...>`
- Factory fixture conventions: `<...>`
- Plain helper/builder conventions: `<...>`
- Fixture naming and location: `<...>`

## Test doubles

- Pytest-native default: `mocker` for behavioral doubles and `monkeypatch` for environment or
  process state.
- Direct `unittest.mock` exception criteria: `<document the rare cases, or state "none">`
- Prefer fake, stub, mock, or real implementation when: `<...>`
- Autospec/spec policy: `<...>`
- Patch-target rule: `<patch the name used by the subject>`
- Contract checks for fakes: `<...>`
- External SDK response fixtures: `<...>`

## Test data and golden files

- Fixture-data location: `<...>`
- Personal/sensitive data restrictions: `<...>`
- Provenance requirements: `<...>`
- Normalized fields: `<...>`
- Golden update command: `<...>`
- Review requirements: `<...>`

## Markers, skips, and expected failures

- Registered markers: `<...>`
- Skip requirements: `<environmental reason>`
- `xfail` requirements: `<issue, owner, strictness, removal condition>`
- Quarantine maximum age: `<...>`

## Quality gates

- Unexpected-warning policy: `<...>`
- Statement coverage floor: `<...>`
- Branch coverage floor: `<...>`
- Changed-code expectation: `<...>`
- Lint/type checks for tests: `<...>`

## Parallelism

- Tests expected to be xdist-safe: `<...>`
- Exclusive-resource markers/groups: `<...>`
- Per-worker resource naming: `<...>`
- Sequential reproduction command: `<...>`

## Commands and CI

- Fast local command: `<...>`
- Unit command: `<...>`
- Integration command: `<...>`
- Coverage command: `<...>`
- Slow/live command: `<...>`
- CI stages and time budgets: `<...>`

## Ownership and maintenance

- Who reviews golden updates: `<...>`
- Who owns live-service tests and budget: `<...>`
- Plugin/version refresh cadence: `<...>`
- Flaky-test response and escalation: `<...>`
