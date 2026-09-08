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

1. **`[active]`** [`justfile-migration`](./features/%5Bactive%5Djustfile-migration.md) — replace the
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

   ➡️ **Promotion milestone:** with the base stable + green, PR `uv_refactor` → `main`, then
   retire `uv_refactor`. (Note: PR-based, updating `EXECUTIVE_SUMMARY.md` §4's original
   force-reset mechanic — decided 2026-09-08.)

## B. Feature branches from the new `main`

3. **`[ready]`** [`ci-release-pipelines`](./features/%5Bready%5Dci-release-pipelines.md) — GitHub
   Actions CI (lint + `ty`, no pytest) + tag-driven releases + `scripts/release.py`. **Started as
   a fresh feature after `main` promotion** (its workflows only go live on `main`/tags).
4. **`[draft]`** [`notebooks-clean-rebuild`](./features/%5Bdraft%5Dnotebooks-clean-rebuild.md) —
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
- **`[draft]`** [`tests-refactor`](./features/%5Bdraft%5Dtests-refactor.md) — triage/group tests,
  rework fixtures+mocks (incl. the anthropic-1.x mock-drift hang), fix the 5 e2e failures, bring
  `tests/` into the ruff+ty gate. Collects the test debt deferred by `justfile-migration`.

## D. Open-source release prep

- **`[backlog]`** open-source release prep — the audit lives in `+planning/opensource_polishing.md`
  (local-only; was expunged from git history in the privacy scrub). See `EXECUTIVE_SUMMARY.md` §2
  for the completed privacy remediation and remaining loose ends.

## Known issues (not yet worth their own feature; tracked here until triaged)

- FFmpeg audio extraction may fail on re-run if output files already exist (missing overwrite
  flag) — see the `refactor_to_cli` spec's Known Issues section.
- **`ty` baseline debt** (from `justfile-migration`, 2026-09-08): 9 errors baselined in 4 src
  files via `[[tool.ty.overrides]]` in `pyproject.toml`. Includes a **latent bug** —
  `anthropic_models.get(model_name)["name"]` in `steps/summarize_transcript.py` subscripts `None`
  for an unknown model. Drive to zero + fix the bug when convenient.
- **tests not in the lint/type gate** (deferred by `justfile-migration`): `tests/` has ~28 lint +
  13 format items of pre-existing debt, plus 5 failing e2e tests (`test_e2e_permutations.py`,
  referencing non-existent step fns) and a fixture-registration issue (`ruff --fix` deletes
  conftest F401 re-imports). All folded into a future **tests-refactor** feature; overlaps
  `orchestrator-retire-baseline`.
