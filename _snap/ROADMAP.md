# Roadmap

Ordered list of features to build for **minutia** — a meeting recording, transcription, and
summarization tool. The order *is* the plan. Detail for any feature lives in its
`features/<name>.md` spec; history lives in [`DECISIONS.md`](./DECISIONS.md).

**Governing brief:** [`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md) (repo root) was the
stabilization plan — freeze a stable base onto `main`, contain scope creep as scoped specs,
rebuild notebooks clean, then re-cut feature branches from `main`. **That plan is now complete:**
the base is on `main`, CI + releases are live, and `v0.3.0` is out. This ROADMAP has been
re-ordered around what comes *after* stabilization.

*Last updated: 2026-11-11 (PLAN: added `[ready]public-release` as the new §Now; the refactor tail
moves to §Then. Earlier, 2026-09-10: BUILD complete: `cli-wizard-redesign` `[active]→[done]` — all 8 tasks +
two live-dogfooding rounds; moved to §Done, pending PR from `cli_commands`. §Now is now the refactor
tail: `eval-seams` → `orchestrator-retire-baseline`. Added `[draft]wizard-tui-progress-and-logs` as
the wizard follow-up polish. Earlier (2026-09-09): PLAN added the redesign spec; reprioritization
reconciled the spine with what shipped (PR #1/#2/#3, v0.2.0 + v0.3.0).)*

---

## ✅ Done — stabilized base + release pipeline (shipped on `main`)

The whole stabilization arc is complete and shipped. Condensed here; narrative in `DECISIONS.md`.

- **`[done]`** [`cli-wizard-redesign`](./features/%5Bdone%5Dcli-wizard-redesign.md) — rebuilt the flat
  `cli.py` into a `cli/` subpackage: bare `minutia` wizard (self-determining, first-run setup +
  guided run), `run pipeline`/`run <step>`, `info`, `setup`; `go`/`process-all`/top-level `config`
  removed; cold-start fix (lazy torch/whisper); wine-palette rich TUI with waveform telemetry + live
  log tail; whisper decode progress; ffmpeg overwrite bug fixed. Added `rich`+`yakh`. Follow-up
  polish parked as `[draft]wizard-tui-progress-and-logs`. *(Completed 2026-09-10; on `cli_commands`,
  pending PR.)*
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

## 🚀 Now — go public

0. **`[ready]`** [`public-release`](./features/%5Bready%5Dpublic-release.md) — finish the
   `public-cleanup` branch (snap workspace local-only, eight small polish commits), fast-forward
   `main`, publish `v0.2.0`–`v0.4.0` + cut `v0.4.1`, flip the repo public. Deliberately small
   (user decision, 2026-11-11): dead code, fixtures and the summarizer rework stay for visible
   work after launch. **Everything below resumes once this ships.**

## 🔨 Then — finish the refactor tail

The CLI polish landed first (user decision, 2026-09-09); the tail is low-risk consolidation that
every future direction wants.

1. **`[ready]`** [`eval-seams`](./features/%5Bready%5Deval-seams.md) — `SummaryClient` protocol +
   `<report>.run.json` run-metadata sidecar. The keystone for the eval branch: unblocks
   `evals-harness` and `local-llm-summarization`, makes runs reproducible/swappable, and its sidecar
   (model, params, cost, hashes per run) is exactly the data the parallel dogfooding wants. Also
   home for the deferred re-run / summarize-as-jobs flow.
2. **`[ready]`** [`orchestrator-retire-baseline`](./features/%5Bready%5Dorchestrator-retire-baseline.md)
   — orchestrator parity, then delete `baseline_pipeline.py`. **Depends on `eval-seams`** (its e2e
   test asserts the run-metadata sidecar). Retires the last pre-orchestrator script path (which
   `cli-wizard-redesign` already drops from the CLI surface) + updates `README.md`.
3. **`[draft]`** [`wizard-tui-progress-and-logs`](./features/%5Bdraft%5Dwizard-tui-progress-and-logs.md)
   — follow-up polish to the wizard TUI (captured from live dogfooding 2026-09-10): unify the
   progress updater and wire it to the TUI, a scrollable full-run log history, un-clip long paths,
   retire the moot `EN` tag. Downstream of `cli-wizard-redesign`; pick up after it closes.

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
- **Promoted 2026-11-11:** open-source release prep is now
  [`public-release`](./features/%5Bready%5Dpublic-release.md) (§Now).
- **`[backlog]`** test-suite + fixtures sprint — benchmark-style fixtures, synthetic-data
  primitives, evals inside the test suite. First sprint after launch; see
  [`BACKLOG.md`](./features/BACKLOG.md).
- **Follow-up:** README screenshot/GIF of the wizard (first commit after going public).

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
