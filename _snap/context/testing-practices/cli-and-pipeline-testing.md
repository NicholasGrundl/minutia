# CLI and Pipeline Testing

This guidance targets a Python CLI that coordinates filesystem operations, local executables,
heavy model work, and an external service. Test each boundary independently, then keep a small
number of complete workflows.

## CLI behavior

Use Typer's `CliRunner` for in-process command behavior:

- Command and option parsing.
- Defaults and validation errors.
- Exit codes.
- User-visible stdout versus stderr.
- Confirmation, cancellation, and noninteractive flags.
- Help output for important public commands.

Avoid asserting an entire Rich-rendered screen unless layout is explicitly contractual. Prefer
important phrases, structured results below the presentation layer, or a normalized snapshot
with a deliberate terminal width and color setting.

Click warns that its testing helpers change interpreter state and are not thread-safe. Keep
runner invocations controlled and use pytest's `tmp_path` with absolute paths rather than the
user's working directory. Click 8.5 deprecates `CliRunner.isolated_filesystem()` in favor of
this approach, so check the installed Click version before maintaining older examples.

## Orchestrator behavior

Test orchestration with small fakes or autospecced collaborators. Valuable scenarios include:

- Steps execute in the required order when order is contractual.
- An existing valid artifact causes the documented skip behavior.
- Force mode reruns only the intended work.
- Failure stops or continues according to policy.
- Paths and options are forwarded correctly.
- Metadata records successful, skipped, and failed stages.

Assert the public result and artifacts first. Assert calls only where coordination itself is the
behavior. Do not make an orchestrator test reproduce every unit test for each stage.

## Filesystem stages

- Use unique `tmp_path` workspaces.
- Build minimal realistic input files.
- Verify both content and naming only when both are public behavior.
- Include collisions, missing parents, invalid extensions, partial output, and force behavior.
- Test atomic-write or cleanup guarantees where interruption could corrupt later runs.
- Normalize temporary prefixes before golden comparisons.

## External executables

Split tests into two layers:

1. Unit tests for command construction, error mapping, and output parsing using a controlled
   runner result.
2. Integration contract tests against the real executable using tiny checked-in inputs.

Real-process tests need a timeout, captured diagnostics, explicit working directory, and a
capability-based skip when the executable is unavailable. A tool being installed should not
automatically turn every unit test into an integration test.

## Heavy local models

Test model-independent transformation and orchestration with a fake transcriber. Keep very few
real-model tests, using the smallest representative model and media fixture that validates the
adapter contract. Mark them clearly and do not place model download or GPU availability on the
default test path.

Separate these concerns:

- Model selection and device policy.
- Client loading/caching.
- Request invocation.
- Transformation of provider segments into project data.
- Persistence of results.

This separation makes most behavior testable without loading a model.

## Remote AI services

Normal unit and integration tests must not send paid API calls. Use a fake client or a
representative SDK-shaped response to cover:

- Request construction.
- Token/cost estimation rules.
- Confirmation and dry-run behavior.
- Successful response parsing.
- Missing or malformed content.
- Authentication, rate-limit, timeout, and provider error translation.
- Output naming and safe persistence.

A live smoke test should be manually or separately triggered, require explicit credentials and
authorization, use a strict cost ceiling, and avoid asserting exact generated prose.

## Configuration tests

Configuration tests are state-isolation tests. For each precedence rule:

- Start from a controlled environment.
- Use temporary config and working directories.
- Set only the values relevant to the scenario.
- Assert both the resolved value and, if exposed publicly, its reported source.
- Cover missing required secrets without embedding a real credential.
- Cover path expansion and platform defaults without depending on the current user.

Reset any settings cache between cases. Prefer constructing a fresh settings object over
mutating module globals.

## Golden scenarios

A pipeline scenario should contain:

- Small source input.
- Expected intermediate artifacts where those formats are public or diagnostically important.
- Expected final deterministic artifact.
- A manifest describing provenance and normalization.

Do not require every test to traverse the full scenario. Reuse the same reviewed data at each
boundary so failures localize to extraction, transcription conversion, merging, or summary
assembly.

## References

- [Typer testing](https://typer.tiangolo.com/tutorial/testing/)
- [Click testing](https://click.palletsprojects.com/en/stable/testing/)
- [Pytest temporary paths](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [Pytest monkeypatching](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [pytest-mock usage](https://pytest-mock.readthedocs.io/en/latest/usage.html)
- [pytest-cov subprocess support](https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html)
