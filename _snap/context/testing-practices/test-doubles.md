# Test Doubles and Boundary Isolation

## Project default: pytest-native test doubles

Stay within the pytest ecosystem for new and refactored tests. Prefer pytest-mock's `mocker`
fixture over importing `Mock`, `MagicMock`, `patch`, or `create_autospec` directly from
`unittest.mock`. Prefer pytest's `monkeypatch` when changing environment or process state.

Pytest-mock is a thin wrapper around the standard-library mock API. Concepts such as
autospeccing, `spec_set`, `side_effect`, patch location, and call objects therefore still come
from `unittest.mock`; consult that documentation to understand behavior, but access those
features through `mocker` in normal project tests. A direct `unittest.mock` import should be an
exception with a concrete reason, not an interchangeable style choice.

## Choose the smallest honest double

The generic word “mock” hides several different tools:

- Stub: returns a controlled value. Useful for a callback or simple boundary response.
- Spy: calls the real implementation while recording interactions.
- Fake: a working, lightweight implementation of an owned interface, such as an in-memory
  repository or deterministic model client.
- Mock: verifies expected interactions.
- Dummy: satisfies a parameter but is not used by the scenario.

Prefer returned-state assertions over interaction assertions unless the interaction is itself
the contract. A fake often gives more resilient use-case tests than many deeply configured
mocks, but it needs contract checks to prevent drift from the real adapter.

## Patch where the name is looked up

Python patching replaces a name in a namespace. Patch the reference used by the subject under
test, not automatically the module where the object was originally defined.

If a module imports `Client` into its own namespace, patch that module's `Client`; patching the
library's original class may have no effect. Prefer object-based patch targets when a direct
reference is available because misspelled string targets fail later and refactor poorly.

## Make mocks fail on interface drift

Use `mocker.patch(..., autospec=True)`, `mocker.create_autospec(...)`, or `spec_set` when
practical. They constrain attributes and call signatures, catching a production API change
that a permissive mock would silently accept.

Do not configure a mock with a large tree of imaginary attributes. Representative response
objects, small typed fakes, or the provider SDK's public types are usually more legible.

Use `side_effect` for a deliberate sequence or exception, not as a miniature hidden program.
Name important mock and stub objects so failure output identifies their role.

## `monkeypatch` versus `mocker`

Use pytest's `monkeypatch` for process and environment state:

- `setenv` and `delenv`.
- `setitem` and `delitem`.
- `chdir`.
- `setattr` for a small replacement function or value.
- `context()` when patch lifetime must be narrower than the test.

Use pytest-mock's `mocker` for behavioral test doubles:

- Call assertions.
- `autospec` and `spec_set`.
- `spy` when the real behavior should still execute.
- `stub` or `async_stub` for callbacks.
- `sentinel` and structured call comparisons.

Both fixtures restore changes automatically. The design question is whether the test needs
environment mutation (`monkeypatch`) or a behavioral double (`mocker`), not whether to switch
between pytest and direct `unittest.mock` styles.

## Prefer explicit seams in controlled code

Global patching is sometimes necessary for third-party APIs, but explicit dependencies are
usually safer in code the project controls. Useful seams include:

- A callable parameter for clock or ID generation.
- A narrow adapter protocol for a remote model client.
- A command runner abstraction that returns a typed result.
- A filesystem path passed by the caller rather than inferred globally.
- A configuration object resolved at the outer boundary.

Do not create an interface solely because a mocking framework makes it fashionable. The seam
should correspond to a genuine ownership, nondeterminism, expense, or side-effect boundary.

## Contract tests for fakes

When both a fake and real implementation exist, define shared behavioral examples and execute
them against both where feasible. At minimum, verify:

- Accepted inputs and defaults.
- Return shape and types.
- Important error behavior.
- Ordering or idempotency guarantees.
- Resource ownership and cleanup.

For a paid or nondeterministic remote API, normal tests should use recorded representative
shapes or SDK-compatible objects without sending requests. A separately authorized smoke test
may check the live boundary; it must never be part of the default suite.

## Common failure modes

- Mocking the function under test rather than its boundary.
- Mixing direct `unittest.mock` patching with pytest-mock without a documented need.
- Asserting every internal call and making refactoring impossible.
- Returning data that the real provider could never return.
- Using a permissive mock that invents attributes on access.
- Sharing a mutable fake across tests without resetting it.
- Patching standard-library or pytest internals broadly.
- Allowing an unrecognized URL, command, or input to receive a generic success response.

A fake should fail loudly on unconfigured operations. Silent generic success can allow a test
to pass while exercising the wrong path.

## References

- [pytest-mock usage](https://pytest-mock.readthedocs.io/en/latest/usage.html)
- [pytest monkeypatching](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [Python `unittest.mock`](https://docs.python.org/3.12/library/unittest.mock.html) — underlying
  API reference; not the preferred direct project interface.
- [Software Engineering at Google: Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html)
- [Cosmic Python: Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository)
