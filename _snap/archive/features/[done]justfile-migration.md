---
state: active         # draft | ready | active | done | deprecated
changelog:
  "2026-09-08": "Initial spec — promoted from BACKLOG's Makefile→justfile item + the ty
    adoption decided in the tooling PLAN session. Dev-facing half of the tooling modernization;
    lands on the base before main promotion. Its sibling is [ready]ci-release-pipelines."
---

# justfile migration + `ty` adoption

## Executive Overview

Replace the `Makefile` with a `justfile` as Minutia's single task runner, and adopt Astral's
`ty` as the project's type checker. This is the **dev-facing half** of the tooling modernization
described in `EXECUTIVE_SUMMARY.md`; the release/CI half is its sibling spec
`[ready]ci-release-pipelines`.

Per the tooling PLAN session (2026-09-08), this lands **now, on the base (`uv_refactor`)** so it
rides along when the base is promoted to `main` — the `just`+`ty` dev loop is part of the stable
base, while the GitHub Actions workflows (which only "go live" once `main` is the real trunk)
are deliberately split into their own post-promotion feature.

Reference: `just` and `ty` usage patterns come from a sibling project, captured at
`_snap/reference/ci_content/justfile`. Cached docs: `_snap/context/just/`, `_snap/context/ty/`,
`_snap/context/uv/`.

**Non-goals**
- **No CI/release workflows** — `.github/`, `release.py`, and `tag-*` recipes belong to
  `[ready]ci-release-pipelines`, started only after `main` promotion.
- **No `direnv`/`.envrc`** — stays a BACKLOG item; not bundled here.
- **No doc rewrites** — the `make`→`just` updates in `AGENTS.md`/`README.md` are **deferred to
  the final stabilization doc pass** (user directive 2026-09-08: docs will churn over the next
  several feature sessions; don't rewrite them until the repo is stable). Deleting the
  `Makefile` while those docs still say `make` leaves them *knowingly* stale until that pass.

## Task Checklist

- [x] Author `justfile` at the repo root, porting the actually-used Makefile targets (target map
      in Details). Verify `just --list` renders and each recipe runs: `just sync`, `just test`,
      `just lint`, `just format`, `just ty`, `just check-all`.
- [x] Add `ty` to the `dev` dependency-group in `pyproject.toml`; add a `ty` recipe
      (`uv run ty check`). — `ty==0.0.79`.
- [x] Run `just ty` once and **record the error count** in `SESSION.md`. Decision checkpoint
      (deferred to build time, per PLAN 2026-09-08): a small count → fix to green; a large count
      → baseline it (per-file `# ty: ignore` / a narrow `[tool.ty]` include) and file a
      follow-up. Either way, `just ty` must exit 0 by the end of this task.
      — **48 → 26 (scoped) → 9 (src-only)**; large count → **baselined** via a narrow per-file
      `[[tool.ty.overrides]]` on 4 src files. `just ty` exits 0. Follow-up filed (see Build notes).
- [x] Wire `ty` into the `check-all` recipe so the dev gate is ruff + ty + test.
- [x] `git rm Makefile` — done (Makefile removed; repo is `just`-only).
- [x] Confirm `just check-all` is green on `uv_refactor`. — **ruff + ty GREEN on `src`**; the
      `test` step surfaces **5 pre-existing e2e failures** that are **deferred** (see Build notes).

## Build notes (2026-09-08)

**Scope decision — gate on `src`, not `src`+`tests`.** `tests/` carries ~28 pre-existing lint
errors + 13 files needing format at HEAD. Cleaning them is test work, and the suite will churn
heavily in the upcoming test refactor, so ruff + ty are scoped to `src` for now; `tests/` is left
untouched and comes into the gate with the future **tests-refactor** feature. (This narrows the
original "src and tests" intent — user-confirmed 2026-09-08.)

**ty baseline (follow-up).** 9 real errors remain in 4 src files (`logging.py`,
`pipeline/orchestrator.py`, `steps/summarize_transcript.py`, `steps/video_extraction.py`),
baselined per-file/per-rule so new errors elsewhere still fail. Driving these to zero includes a
**genuine latent bug**: `anthropic_models.get(model_name)["name"]` in `summarize_transcript.py`
subscripts `None` when the model is unknown (ty: `not-subscriptable`).

**Deferred to the tests-refactor feature:**
- 5 e2e failures in `test_e2e_permutations.py` — call `audio_transcription.transcribe_audio_files`
  / `summarize_transcript.summarize_run`, which don't exist (ty flagged the same). Overlaps
  `orchestrator-retire-baseline`.
- Idiomatic pytest fixture registration — `ruff check --fix` deletes the fixture re-imports in
  `tests/*/conftest.py` (F401). Switch to `pytest_plugins = [...]` before putting tests in the
  mutating `ruff` recipe.

**Dropped Makefile targets:** `commit` (broken), `test-codex`/`lint-codex` (re-add only if the
Codex sandbox issue recurs), `install-jupyter` (use `just sync-all` or `uv sync --group jupyter`).

## Details

### Target map (Makefile → justfile)

Ported (renamed to the lean `just` idiom):

| Makefile target | justfile recipe | Notes |
|---|---|---|
| `install` / `install-all` | `sync` | `uv sync` (default dev group); `sync-all` → `--all-groups` |
| `lint` | `lint` | `uv run ruff check .` (read-only) |
| `format` | `format` | `uv run ruff format .` |
| `lint-fix` | `ruff` | mutating: `ruff format .` + `ruff check --fix .` |
| — | `ty` | **new**: `uv run ty check` |
| `check-all` | `check-all` | ruff + `ty` + test (dev gate) |
| `test` (+ tiers) | `test *args` | `uv run pytest {{args}}`; keep `test-unit`/`test-integration`/`test-all`/`test-cov` convenience recipes |
| `create-env-file` | `create-env-file` | port the `.env` scaffold |
| `jupyter` | `jupyter` | `uv run jupyter lab --autoreload` |
| `clean` / `test-cleanup` | `clean` | rm build + test artifacts |

**Dropped:**
- `commit` — already broken (pointed at a deleted hook); MACRO commits are now `/snap-git`.
- `test-codex` / `lint-codex` — sandbox `uv run` workarounds. Leave out initially; re-add a
  `.venv/bin/python`-direct recipe only if the Codex permission issue still bites.

### `ty` adoption

`ty` is Astral's type checker (fast, `uv`-native), chosen over `mypy` (2026-09-08 PLAN) to match
the sibling project and the reference tooling. This **supersedes** the "mypy someday" note in
`AGENTS.md` — that note gets corrected in the deferred doc pass. Expect a first-run triage: the
error count decides fix-now vs. baseline (checklist item above). See `_snap/context/ty/`.

### Sequencing

`justfile-migration` → stabilize the base → PR `uv_refactor` → `main`. Only after `main` is the
real trunk does `ci-release-pipelines` begin (its `ci.yml` fires on `main`; its `release.yml` on
tags). See `EXECUTIVE_SUMMARY.md` §4/§7.
