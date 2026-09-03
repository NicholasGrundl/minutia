# Minutia — Executive Summary & Stabilization Plan

*Checkpoint: 2026-09-03. Author: repo maintainer + agent pairing.*

> **Purpose of this doc.** This is a decision-and-guidance brief, not a spec. It captures
> where Minutia actually stands at this checkpoint, then lays out the plan to **stabilize the
> current work onto `main`**, **move every in-flight / partial design into `_snap/features/`**,
> **rebuild the notebooks clean**, and **re-cut feature branches from a stable base** so scope
> creep is contained and the tool is immediately usable. Detailed specs live in
> `_snap/features/`; this doc is the map that points at them.

---

## 1. What Minutia is

A meeting recording → transcription → summarization tool. It extracts per-track audio from
OBS-recorded MKVs (ffmpeg), transcribes with Whisper, merges tracks chronologically, and
generates an AI-named markdown summary via Anthropic Claude (with a local-LLM path on the
horizon). It is mid-migration from a **notebook-driven workflow** to a **`src/minutia/` package
+ `typer` CLI**.

---

## 2. Where the repo stands right now (the honest state)

### 2a. Just completed — privacy remediation ✅
Real client meeting content and recordings were expunged from **all** git history via
`git-filter-repo` and force-pushed:
- Removed: `notebooks/`, `planning/` (incl. `example_data/` client meeting + a real `.mkv`),
  `test_recording.wav`, `opensource_polishing.md`.
- Verified: zero PII across all history blobs; core tree (`src/`, `tests/`, `_snap/`) intact.
- Working copies preserved locally, gitignored: **`+notebooks/`**, **`+planning/`**.
- Safety net: **`../minutia-backup.git`** (full pre-rewrite mirror — *still contains the PII,
  never push or share it; delete once confident*).
- `backup-uv_refactor` is a **local-only** branch that still carries the old PII — **never
  push it**.

### 2b. Branch reality
| Branch | Tip | Reality |
|---|---|---|
| `main` | `6ee0ea6` (Initial commit only) | **Stale / divergent.** Does *not* reflect the project. |
| `uv_refactor` | `7ba0a7b` | **The real project.** All work lives here; in sync with remote. |
| `backup-uv_refactor` | local | PII-bearing safety branch. Do not push. |

➡️ **The core structural problem: `main` is empty and all real work sits on a long-lived
feature branch that has absorbed multiple concerns.** This plan fixes that.

### 2c. What's built (on `uv_refactor`)
- `src/minutia/` package: `cli.py` (typer), `config.py` (layered precedence + `minutia config`),
  `paths.py` (`RunPaths`, latest-MKV discovery), `prompts.py` (6-kind registry),
  `run_metadata.py`, `model_registry.py`, `logging.py`.
- `steps/`: `video_extraction`, `audio_transcription`, `transcript_merger`,
  `summarize_transcript` — one concern each.
- `pipeline/orchestrator.py`, `clients/` (scaffold, empty).
- `tests/` three-tier (`unit`/`integration`/`slow`) + golden-sample fixtures.
- Working CLI: `minutia go | config | extract-audio | transcribe | merge-transcripts |
  summarize | process-all`.

### 2d. What's in-flight / partial (the loose ends)
- **`refactor_to_cli`** (`_snap/features/[active]refactor_to_cli.md`): Phases 0–4 code **DONE**;
  **pending** → the live milestone (run one real meeting **CLI-only**, then retire the
  notebook), **Phase 5** (eval seams: `SummaryClient` protocol, run-metadata sidecar),
  **Phase 6** (orchestrator hardening + delete `baseline_pipeline.py`).
- **`baseline_pipeline.py`** still present and **still the entry point documented in
  `README.md`** (README also references a real recording filename and a stale test path).
- **Notebooks** expunged from git; local-only in `+notebooks/`. They were the daily driver
  *and* mixed dev/prod/real-data — to be **rebuilt clean** (§5).
- **`refactor_for_opensource_portfolio`** (`[draft]`): the broad vision — filestore for
  videos, SQL job/transcript tracking, background-process CLI, local-LLM summarization, evals
  harness. **This is the main source of scope creep** and must stay parked as scoped drafts,
  not bled into the stable base.
- Minor: stray `src/minutia/.ipynb_checkpoints/` on disk (not tracked — fine), the previously
  broken `make commit` target.

---

## 3. The goal of this stabilization pass

1. **Freeze a stable, usable base and put it on `main`** — so `main` is the truth and always
   runnable.
2. **Contain scope creep** — everything not part of the stable base becomes a *named,
   scoped* item in `_snap/features/`, built later on its own branch.
3. **Rebuild the notebooks clean** — synthetic data only, outputs cleared, never the daily
   driver again.
4. **Re-cut feature branches from `main`** — one concern per branch, small merges, `main`
   never broken.

---

## 4. Consolidate to `main` NOW

**Define the "stable base" = current `uv_refactor` (`7ba0a7b`), with these loose ends either
finished or explicitly deferred (not half-done in the tree):**

- [ ] **Decide `baseline_pipeline.py`'s fate for the base.** It is still referenced by
      `README.md` and a smoke test, so it can't just be deleted mid-air. Two clean options:
      **(a)** keep it as the documented entry point for the base and defer deletion to the
      Phase 6 branch, or **(b)** promote the CLI to the documented entry point now and move
      `baseline_pipeline.py` behind a "legacy" note. **Pick one before promoting `main`.**
- [ ] **Fix `README.md`** to match reality (CLI as entry point; remove the real-recording
      example filename `+recordings/…meetingnotes.mkv`; fix the stale
      `tests/test_baseline_pipeline.py` path).
- [ ] **Confirm the base is green**: `make check-all` (lint-fix + format + test) passes.
- [ ] **Confirm no notebook references dangle** in `src/`, `README.md`, or `AGENTS.md` now
      that `notebooks/` is gone from git (they live in `+notebooks/` locally).

**Promotion mechanics (maintainer runs these; agent will hand exact commands):** because `main`
is a stale divergent initial commit, the clean move is to **make `main` point at the stabilized
`uv_refactor` state** (fast-forward-by-reset + force-push `main`), then treat `main` as the
protected trunk. Keep `uv_refactor` only until `main` is confirmed, then retire it. *(Exact git
sequence to be produced when the checklist above is green — this is a history-affecting op on
`main`, so it gets its own confirmation step, same as the privacy rewrite.)*

---

## 5. Move every in-flight design into `_snap/features/`

**Principle: nothing half-built lives loose in the tree — every partial becomes a spec.**
Most already live in `_snap/features/`; this pass formalizes the split so the stable base
carries no ambiguous "in progress" surface:

- **Keep active:** `[active]refactor_to_cli.md` — but **split its unfinished tail** into its
  own scoped items so it can be *closed* at the base:
  - `finish-cli-parity` — the live milestone (one real meeting, CLI-only) + notebook retirement.
  - `eval-seams` — Phase 5 (`SummaryClient` protocol + run-metadata sidecar).
  - `orchestrator-retire-baseline` — Phase 6 (orchestrator wiring + `baseline_pipeline.py`
    deletion + README).
- **Keep parked (scope-creep containment):** promote the big `[draft]refactor_for_opensource_portfolio`
  bullets into **separate scoped drafts**, each pulled into active work only on its own branch:
  video filestore · SQL job/transcript tracking · background-process CLI · local-LLM
  summarization · evals harness.
- **New spec:** `notebooks-clean-rebuild` (see §5 → §6). 
- **Housekeeping already tracked** in `_snap/features/BACKLOG.md`: Makefile→justfile + direnv,
  guided TUI, `context/` pruning. Leave in BACKLOG until triggered.
- Update `_snap/ROADMAP.md` to reflect the new ordering, and log this consolidation in
  `_snap/DECISIONS.md`.

---

## 6. Rebuild the notebooks — clean this time

**Why:** the old notebooks carried real meeting PII, mixed dev/experiment/production concerns,
committed cell outputs (leaking transcripts), and quietly became the *daily driver*. They are
now out of git history; local copies are salvage-only in `+notebooks/`.

**Target policy for the new `notebooks/`:**
- **Synthetic / public data only** — never a real recording or transcript. Reuse the
  `tests/fixtures/scenarios/` golden samples as the demo inputs.
- **Outputs cleared on commit** — add an `nbstripout` (or equivalent) step; keep
  `.ipynb_checkpoints/` gitignored (already is).
- **Thin notebooks over the package** — notebooks *demonstrate* `minutia.steps.*` /
  `minutia.prompts` / the CLI; they never re-implement pipeline logic (that logic already
  lives in `src/`).
- **A small, purposeful set**, e.g.: `01_quickstart_demo.ipynb` (end-to-end on a fixture),
  `02_prompt_kinds_tour.ipynb`, `03_transcription_experiments.ipynb` (the eval sandbox — this
  is where new STT/summarizer ideas get tried before touching the package).
- **Salvage from `+notebooks/`**: harvest still-useful experiment cells (Whisper arg tuning,
  faster-whisper/WhisperX/pyannote scaffolds captured in `+planning/transcription_experiments.md`)
  into `03_…`, rewritten against synthetic audio.

Track this as `_snap/features/notebooks-clean-rebuild.md`; build it on its own branch off the
new `main`.

---

## 7. Feature-branch strategy from the stable base

Once `main` is stabilized (§4):
- **One concern per branch, cut from `main`**, named for its `_snap` spec. Suggested order:
  1. `notebooks-clean-rebuild` (fast, unblocks daily use + demos)
  2. `finish-cli-parity` (retire the notebook-as-driver for real)
  3. `eval-seams`
  4. `orchestrator-retire-baseline` (deletes `baseline_pipeline.py`)
  5. then the parked `opensource_portfolio` items, each on its own branch.
- **Small, reviewable merges back to `main`**; `main` stays runnable at every merge.
- **No long-lived catch-all branch again** — the `uv_refactor` sprawl is exactly what this
  plan retires.

---

## 8. Immediate next actions (ordered)

1. [ ] Decide `baseline_pipeline.py` fate for the base (§4).
2. [ ] Fix `README.md` + purge stale notebook/recording references (§4).
3. [ ] `make check-all` green on `uv_refactor`.
4. [ ] Split `refactor_to_cli`'s tail + park `opensource_portfolio` items as scoped specs;
       add `notebooks-clean-rebuild`; update `ROADMAP.md` + `DECISIONS.md` (§5).
5. [ ] Promote stabilized `uv_refactor` → `main`; confirm remote; retire `uv_refactor` (§4).
6. [ ] Delete `backup-uv_refactor` and `../minutia-backup.git` **only after** `main` is
       confirmed good and you're satisfied the scrub is clean.
7. [ ] Cut the first feature branch (`notebooks-clean-rebuild`) from the new `main` (§6–§7).

---

## Appendix — reference pointers

- Active spec: `_snap/features/[active]refactor_to_cli.md`
- Vision / scope-creep parking lot: `_snap/features/[draft]refactor_for_opensource_portfolio.md`
- Backlog: `_snap/features/BACKLOG.md` · Roadmap: `_snap/ROADMAP.md` · History: `_snap/DECISIONS.md`
- Salvage: `+notebooks/` (old notebooks), `+planning/` (incl. `transcription_experiments.md`,
  `design-doc-meeting-recorder.md`)
- Backup mirror (PII — do not push/share): `../minutia-backup.git`
