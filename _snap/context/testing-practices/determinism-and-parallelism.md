# Determinism and Parallelism

## Determinism is a design requirement

A trustworthy test produces the same outcome when it is:

- Run alone by node ID.
- Run after any other test.
- Run repeatedly.
- Collected in a different order.
- Run on another supported machine.
- Distributed across workers, if marked parallel-safe.

Failures should include enough information to reproduce the exact case locally.

## Control hidden inputs

Common hidden inputs include:

- Current time, timezone, locale, and daylight-saving transitions.
- Random numbers, generated IDs, and unordered collections.
- Current directory, environment variables, and user config.
- User home directories and platform default paths.
- Existing files and shared output directories.
- CPU/GPU availability and thread counts.
- Network, DNS, provider state, and credentials.
- Global logging handlers, module caches, and singleton clients.

Prefer dependency injection or narrow patches. Restore all changed process state. Use sorted
input when collection or output order matters. Avoid timing assertions based on `sleep`; use a
controllable clock, events, or bounded polling with a diagnostic timeout.

## Detect order dependence

Useful checks during suite hardening:

- Run an individual failing node ID.
- Run the containing module in normal and reversed/randomized order.
- Repeat suspected cases.
- Compare sequential and distributed execution.
- Ensure a test does not rely on output from an earlier test.

Random-order plugins can expose contamination but do not repair it. Always retain the seed from
a failed run and convert the discovered problem into an isolated regression test.

## Parallel execution with xdist

Xdist creates worker processes. Each worker performs collection, and the controller requires
all workers to collect the same tests in the same order. Therefore:

- Do not parametrize from sets or other unordered sources.
- Do not generate cases from mutable external state during collection.
- Give each worker unique ports, databases, caches, output paths, or account names.
- Treat session scope as per worker.
- Use the run UID when a resource must be shared across workers.
- Use an inter-process lock only when a resource genuinely must be initialized once globally.
- Choose `loadscope`, `loadfile`, or `loadgroup` when expensive fixtures or exclusive resources
  require related tests to stay together.

The default `load` mode does not guarantee execution order. This is an advantage for exposing
hidden coupling, but failures should be reproduced without distribution for ordinary debugging.
Xdist also limits live stdout/stderr and interactive debugger behavior.

## Thread and process safety

Pytest itself normally runs tests sequentially in one thread. Application-created threads must
be joined during teardown. Do not invoke pytest assertion helpers concurrently from multiple
threads because pytest documents them as not thread-safe.

For subprocesses:

- Always set a timeout.
- Capture stdout and stderr for failure diagnostics.
- Assert exit status before interpreting output.
- Pass an explicit environment and working directory when behavior depends on them.
- Terminate and reap child processes during fixture cleanup.
- Use unique paths per test or worker.

## Flaky-test response

1. Preserve the failure output, node ID, environment, and random seed.
2. Determine whether the cause is uncontrolled input, leaked state, timing, concurrency, or an
   overly strict assertion.
3. Reproduce at the narrowest boundary.
4. Fix isolation or synchronization.
5. Add a deterministic regression test.

Retries may collect evidence during investigation but should not become the default definition
of passing. A non-strict `xfail` can hide unexpected passes as well as failures and should be a
short-lived quarantine with an owner and removal condition.

## References

- [Pytest flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html)
- [pytest-xdist distribution modes](https://pytest-xdist.readthedocs.io/en/stable/distribution.html)
- [pytest-xdist how-tos](https://pytest-xdist.readthedocs.io/en/stable/how-to.html)
- [pytest-xdist limitations](https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html)
- [Hypothesis flaky failures](https://hypothesis.readthedocs.io/en/latest/tutorial/flaky.html)

