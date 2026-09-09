# Roadmap

Ordered list of features to build for **minutia** — a meeting recording, transcription, and
summarization tool. The order *is* the plan; "phases" are just grouping labels. Detail for any
feature lives in its `features/<name>.md` spec; history lives in
[`DECISIONS.md`](./DECISIONS.md).

**Governing brief:** [`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md) (repo root) is the
stabilization plan this ordering operationalizes — freeze a stable base onto `main`, contain
scope creep as scoped specs, rebuild notebooks clean, then re-cut feature branches from `main`.

*Last updated: 2026-09-08 (tooling PLAN session: added the `just`/`ty` + CI/release specs; split
`refactor_to_cli`'s tail into `finish-cli-parity` / `eval-seams` / `orchestrator-retire-baseline`;
parked the portfolio vision as scoped `[draft]` stubs; added `notebooks-clean-rebuild`).*

---

## A. Stabilize the base, then promote to `main`

1. **`[done]`** [`justfile-migration`](./features/%5Bdone%5Djustfile-migration.md) — replace the
   `Makefile` with a `justfile` and adopt `ty` for type-checking. **Lands on the base
   (`uv_refactor`) now**, so it rides along at promotion. Code done 2026-09-08 (justfile authored;
   `ty` adopted + baselined; gate scoped to `src`). Closes once the user runs the `git mv`
   (`[ready]→[active]`... then `→[done]`) + `git rm Makefile`. Tests deferred (see below).
2. **`[active]`** [`refactor_to_cli`](./features/%5Bactive%5Drefactor_to_cli.md) — Phases 0–4 code
   **DONE** (2026-07-02). Its unfinished tail is now split into the three specs below; it closes
   (`→[done]`) when `finish-cli-parity`'s milestone passes.
   - **`[ready]`** [`finish-cli-parity`](./features/%5Bready%5Dfinish-cli-parity.md) — the live
     milestone: one real meeting CLI-only, then retire the notebook as daily driver.
   - **`[ready]`** [`eval-seams`](./features/%5Bready%5Deval-seams.md) — `SummaryClient` protocol
     + run-metadata sidecar (was Phase 5).
   - **`[ready]`** [`orchestrator-retire-baseline`](./features/%5Bready%5Dorchestrator-retire-baseline.md)
     — orchestrator parity + delete `baseline_pipeline.py` (was Phase 6).
3. **`[done]`** [`settings-resolution`](./features/%5Bdone%5Dsettings-resolution.md) — replace
   the stateful dotenv loader with Pydantic Settings; retain the platformdirs global config,
   discover one cwd-contextual `.env`, expose explicit dotenv controls, preserve provenance, and
   isolate tests from ambient configuration. Pipeline YAML/JSON remains a separate future domain.

   ➡️ **Promotion milestone:** with the base stable + green, PR `uv_refactor` → `main`, then
   retire `uv_refactor`. (Note: PR-based, updating `EXECUTIVE_SUMMARY.md` §4's original
   force-reset mechanic — decided 2026-09-08.)
   **Before the PR (added 2026-09-08 after CLI dogfooding):** (1) update `README.md` (make→just,
   install/usage, anthropic 1.x + python `<3.14` notes); (2) ~~a once-through of the tests together
   (triage/group + rework fixtures/mocks — see `[draft]tests-refactor.md`)~~ **DONE 2026-09-08** —
   `tests-refactor` is checklist-complete (tiered by directory, `tests/` in the ruff + ty gate, 97
   green). Only (1) `README.md` remains before the PR.

## B. Feature branches from the new `main`

4. **`[ready]`** [`ci-release-pipelines`](./features/%5Bready%5Dci-release-pipelines.md) — GitHub
   Actions CI (lint + `ty`, no pytest) + tag-driven releases + `scripts/release.py`. **Started as
   a fresh feature after `main` promotion** (its workflows only go live on `main`/tags).
5. **`[draft]`** [`notebooks-clean-rebuild`](./features/%5Bdraft%5Dnotebooks-clean-rebuild.md) —
   rebuild `notebooks/` on synthetic data, outputs stripped, thin over the package (§6). §7's
   suggested first branch off the new `main`.

## C. Parked vision (scope-creep containment — each expands on its own branch)

Split out of the former `refactor_for_opensource_portfolio` draft (kept as the vision/index):

- **`[draft]`** [`video-filestore`](./features/%5Bdraft%5Dvideo-filestore.md)
- **`[draft]`** [`sql-job-tracking`](./features/%5Bdraft%5Dsql-job-tracking.md)
- **`[draft]`** [`background-process-cli`](./features/%5Bdraft%5Dbackground-process-cli.md)
- **`[draft]`** [`local-llm-summarization`](./features/%5Bdraft%5Dlocal-llm-summarization.md)
  (depends on `eval-seams`)
- **`[draft]`** [`evals-harness`](./features/%5Bdraft%5Devals-harness.md) (depends on `eval-seams`)
- **`[done]`** [`tests-refactor`](./features/%5Bdone%5Dtests-refactor.md) — **checklist-complete
  2026-09-08** (awaiting the `[draft]→[done]` git mv): triaged/grouped tests by directory,
  reworked fixtures+mocks (incl. the anthropic-1.x mock drift), fixed the 5 e2e failures, and
  brought `tests/` into the ruff+ty gate (13 ty diagnostics baselined). Collected the test debt
  deferred by `justfile-migration`.

## D. Open-source release prep

- **`[backlog]`** open-source release prep — the audit lives in `+planning/opensource_polishing.md`
  (local-only; was expunged from git history in the privacy scrub). See `EXECUTIVE_SUMMARY.md` §2
  for the completed privacy remediation and remaining loose ends.

## Known issues (not yet worth their own feature; tracked here until triaged)

- FFmpeg audio extraction may fail on re-run if output files already exist (missing overwrite
  flag) — see the `refactor_to_cli` spec's Known Issues section.
- **`ty` baseline debt** (2026-09-08): **9 src errors** (from `justfile-migration`, 4 src files) +
  **13 test errors** (from `tests-refactor` — dynamic-pattern inference gaps in `conftest.py`,
  `test_prompts.py`, `test_cli_process_all.py`), all baselined via `[[tool.ty.overrides]]` in
  `pyproject.toml`. The src set includes a **latent bug** —
  `anthropic_models.get(model_name)["name"]` in `steps/summarize_transcript.py` subscripts `None`
  for an unknown model. Drive both baselines to zero + fix the bug when convenient (the test set is
  tightenable by annotating the seams: a `Callable`/`Protocol` return for `get_prompt_builder`, an
  explicit type on the capture dict).
- ~~**tests not in the lint/type gate**~~ **RESOLVED 2026-09-08 (tests-refactor):** `tests/` is now
  in the ruff + ty gate (recipes run `src tests`; `[tool.ty.src]` includes `tests`, excludes
  `tests/scripts/`). 13 ty diagnostics were baselined via `[[tool.ty.overrides]]` — driving both ty
  baselines (9 src + 13 tests) to zero remains follow-up debt below.
