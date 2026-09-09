# Roadmap

Ordered list of features to build for **minutia** — a meeting recording, transcription, and
summarization tool. The order *is* the plan. Detail for any feature lives in its
`features/<name>.md` spec; history lives in [`DECISIONS.md`](./DECISIONS.md).

**Governing brief:** [`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md) (repo root) was the
stabilization plan — freeze a stable base onto `main`, contain scope creep as scoped specs,
rebuild notebooks clean, then re-cut feature branches from `main`. **That plan is now complete:**
the base is on `main`, CI + releases are live, and `v0.3.0` is out. This ROADMAP has been
re-ordered around what comes *after* stabilization.

*Last updated: 2026-09-09 (PLAN session: added `[ready]cli-wizard-redesign` — CLI subpackage + rich
wizard modeled on the sibling-project reference — and prioritized it FIRST in §Now, ahead of the tail.
Earlier same day: reprioritization session reconciled the spine with what shipped (promotion PR #1,
ci-release-pipelines PR #2, CPU-torch PR #3, releases v0.2.0 + v0.3.0) and restructured
Done/Now/Next; decision to dogfood in parallel and defer the §C vision to a post-tail checkpoint.)*

---

## ✅ Done — stabilized base + release pipeline (shipped on `main`)

The whole stabilization arc is complete and shipped. Condensed here; narrative in `DECISIONS.md`.

- **`[done]`** [`justfile-migration`](./archive/features/%5Bdone%5Djustfile-migration.md) — `Makefile` →
  `justfile`; adopted `ty`.
- **`[done]`** [`refactor_to_cli`](./archive/features/%5Bdone%5Drefactor_to_cli.md) — Phases 0–4; CLI is
  the daily driver. Tail split into `finish-cli-parity` (done) + the two `[ready]` specs below.
- **`[done]`** [`finish-cli-parity`](./archive/features/%5Bdone%5Dfinish-cli-parity.md) — real meeting run
  CLI-only via `minutia go`; notebook retired as daily driver.
- **`[done]`** [`settings-resolution`](./archive/features/%5Bdone%5Dsettings-resolution.md) — Pydantic
  Settings; deterministic precedence; tests isolated from ambient config.
- **`[done]`** [`tests-refactor`](./archive/features/%5Bdone%5Dtests-refactor.md) — tiered suite
  (unit/integration/slow); `tests/` in the ruff + ty gate.
- **`[done]`** [`ci-release-pipelines`](./archive/features/%5Bdone%5Dci-release-pipelines.md) — GitHub
  Actions CI (lint + `ty`, no pytest) + tag-driven releases + `scripts/release.py`. Merged PR #2;
  workflows live on `main`. **v0.2.0 + v0.3.0 released** (v0.3.0 carries PR #3's CPU-only-torch CI
  fix). *Awaiting the `[active]→[done]` git mv rename.*

**Milestones hit:** `uv_refactor → main` promotion (PR #1, `uv_refactor` retired); base green
(ruff + ty + 100 pytest); CLI validated on a real meeting; CI gating `main`; reproducible tagged
releases; `pyproject` at `0.3.0`.

## 🔨 Now — polish the CLI, then finish the refactor tail

The CLI is where the tool is actually used, so it goes **first** (user decision, 2026-09-09);
the tail is low-risk consolidation that every future direction wants.

1. **`[active]`** [`cli-wizard-redesign`](./features/%5Bactive%5Dcli-wizard-redesign.md) — **in
   progress** (flipped `[ready]→[active]` 2026-09-09; BUILD on task 1, scaffold the `cli/` package).
   Rebuild the flat `cli.py` into a `cli/` subpackage with a concise top-level surface
   (`run` / `setup` / `info`) and a full-screen **rich wizard**, modeled on the sibling-project reference
   (`_snap/reference/+cli_content/cli/`). Bare `minutia` self-determines (guided run, or first-run
   setup that persists the API key + recordings dir, then runs); first-class notes panel; cold-start
   fix (lazy torch/whisper). Drops `go`/`process-all` from the surface. Adds `rich` + `yakh`.
   *→ next BUILD session flips this `[ready]→[active]`.*
2. **`[ready]`** [`eval-seams`](./features/%5Bready%5Deval-seams.md) — `SummaryClient` protocol +
   `<report>.run.json` run-metadata sidecar. The keystone for the eval branch: unblocks
   `evals-harness` and `local-llm-summarization`, makes runs reproducible/swappable, and its sidecar
   (model, params, cost, hashes per run) is exactly the data the parallel dogfooding wants. Also
   home for the deferred re-run / summarize-as-jobs flow.
3. **`[ready]`** [`orchestrator-retire-baseline`](./features/%5Bready%5Dorchestrator-retire-baseline.md)
   — orchestrator parity, then delete `baseline_pipeline.py`. **Depends on `eval-seams`** (its e2e
   test asserts the run-metadata sidecar). Retires the last pre-orchestrator script path (which
   `cli-wizard-redesign` already drops from the CLI surface) + updates `README.md`.

## 🐕 In parallel — dogfooding

Use the CLI on real meetings while the tail gets built (user decision, 2026-09-09). Findings go to
**[`reference/dogfood-findings.md`](./reference/dogfood-findings.md)** — a running log that feeds
the expansion decision below. Route findings by type: bugs → "Known issues" here; feature ideas →
`features/BACKLOG.md`; direction-shaping signals → the checkpoint below.

## 🧭 Next — expansion checkpoint (decide after the tail, steered by dogfooding)

The parked vision (former `refactor_for_opensource_portfolio`, kept as the vision/index). Each
expands on its own branch off `main`. **Order is not yet committed** — pick from dogfooding
findings once the tail lands.

- **`[draft]`** [`obs_launcher_and_wrapper`](./features/%5Bdraft%5Dobs_launcher_and_wrapper.md) —
  OBS-driven recorder CLI (`reccli`); extends minutia *upstream* into capturing the recording
  (today's manual "step 0"). *Newest draft; not previously on the ROADMAP.*
- **`[draft]`** [`background-process-cli`](./features/%5Bdraft%5Dbackground-process-cli.md) —
  long steps run in the background.
- **`[draft]`** [`sql-job-tracking`](./features/%5Bdraft%5Dsql-job-tracking.md) — jobs/transcripts
  in a DB.
- **`[draft]`** [`video-filestore`](./features/%5Bdraft%5Dvideo-filestore.md) — managed store for
  recordings.
- **`[draft]`** [`local-llm-summarization`](./features/%5Bdraft%5Dlocal-llm-summarization.md) —
  **needs `eval-seams`** (swap in a local `SummaryClient`).
- **`[draft]`** [`evals-harness`](./features/%5Bdraft%5Devals-harness.md) — **needs `eval-seams`**
  (score summarization/transcription alternatives).

## 📦 Later — open-source release prep

- **`[draft]`** [`notebooks-clean-rebuild`](./features/%5Bdraft%5Dnotebooks-clean-rebuild.md) —
  rebuild `notebooks/` on synthetic data, outputs stripped, thin over the package.
- **`[backlog]`** open-source release prep — audit in `+planning/opensource_polishing.md`
  (local-only). See `EXECUTIVE_SUMMARY.md` §2 for completed privacy work + loose ends.

## Known issues (tracked here until they earn a feature)

- FFmpeg audio extraction may fail on re-run if output files already exist (missing overwrite
  flag) — see the `refactor_to_cli` spec's Known Issues.
- **`ty` baseline debt** (2026-09-08): **9 src errors** (4 files) + **13 test errors**, all
  baselined via `[[tool.ty.overrides]]` in `pyproject.toml`. The src set includes a **latent bug**
  — `anthropic_models.get(model_name)["name"]` in `steps/summarize_transcript.py` subscripts
  `None` for an unknown model. Drive both baselines to zero + fix the bug when convenient
  (`eval-seams` touches this summarize path — a natural time to clean the seams).
- **Stale `BACKLOG.md` / `context/` drift** (flagged 2026-09-09): `BACKLOG.md` holds items from an
  unrelated project (LanceDB/metrochat/SDS retrieval, D3 web-app `context/` folders). Prune in a
  future ALIGN pass.
