---
state: draft
changelog:
  "2026-09-08": "Initial stub — collects the test-suite work deferred by
    justfile-migration (gate scoping, failing e2e tests, fixture-registration gotcha) plus the
    anthropic 1.x mock-drift hang found while fixing the summarize call."
---

# tests-refactor (parked)

## Executive Overview

Triage, group, and rework Minutia's test suite so it is trustworthy and cheap to run: fix or
retire the broken tests, rebuild the fixtures/mocks against the *current* dependency versions,
and bring `tests/` into the ruff + ty gate. The suite churns heavily right now (mid-refactor),
so this is deliberately deferred until the code under it stabilizes.

**Guiding principle:** don't run the full suite as the default feedback loop — group tests
(fast unit vs. slower integration vs. real-model slow) so day-to-day work runs a fast subset.

## Task Checklist

- [ ] **Triage & group** every test into `unit` / `integration` / `slow`; mark or delete dead
      tests. Make a fast default subset the normal loop; the full suite is opt-in.
- [ ] **Rework fixtures & mocks** — rebuild `tests/mocks/` against current deps; register mock
      fixtures the idiomatic pytest way (`pytest_plugins`) instead of conftest re-imports that
      `ruff --fix` deletes (F401).
- [ ] **Fix the 5 e2e failures** in `test_e2e_permutations.py` — they call step functions that
      don't exist (`audio_transcription.transcribe_audio_files`, `summarize_transcript.summarize_run`);
      align to the real interface. Overlaps `orchestrator-retire-baseline`.
- [ ] **Fix the anthropic-1.x mock drift** (see Details) — the LLM mock lets a real API call
      through under anthropic 1.x, hanging the full suite.
- [ ] **Bring `tests/` into the gate** — clean the ~28 lint + 13 format items and re-scope
      ruff + ty to `src` + `tests` (justfile-migration gated on `src` only).

## Details

### Deferred from justfile-migration (2026-09-08)
- Gate is `src`-only; `tests/` has ~28 lint + 13 format items of pre-existing debt.
- `ruff check --fix` deletes conftest fixture re-imports (F401) — the reason tests are kept out
  of the mutating `ruff` recipe until fixtures are registered via `pytest_plugins`.
- 5 pre-existing e2e failures (`test_e2e_permutations.py`) referencing non-existent step fns.

### anthropic 1.x mock drift → full-suite hang (found 2026-09-08)
While fixing the `summarize` call for the anthropic `0.x → 1.x` bump, the **full test suite
(one process) began to hang** (it ran in ~3s before the bump). Isolated facts:
- `tests/unit` alone: 61 passed, ~1.4s. `tests/integration` + `tests/test_mocks_sanity.py`
  alone: 13 passed / 5 failed, ~2.65s. Collection: 79 tests, 0.55s. **No hang in the subsets.**
- Only the full run-in-one-process hangs, and only *after* moving to anthropic 1.4.0.
- **Hypothesis:** `tests/mocks/llm_mock.py` is 0.x-shaped and no longer intercepts under
  anthropic 1.x, so under some ordering a test constructs a real `Anthropic()` client and makes
  a **real `messages.create` call** (ANTHROPIC_API_KEY is set), hanging on the SDK's retry/
  timeout (default 10 min). Not yet confirmed by pinning down the exact test.
- **Do not** debug by re-running the full suite (slow + spends real money if it does call out);
  find the offending test with a per-test timeout and an offline/empty API key first.
