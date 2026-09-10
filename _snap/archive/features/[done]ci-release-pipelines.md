---
state: done          # draft | ready | active | done | deprecated
changelog:
  "2026-09-08": "Initial spec — the release/CI half of the tooling modernization. Blocked by
    main promotion; started as a fresh feature once main is the real trunk. Sibling of
    [ready]justfile-migration."
  "2026-09-09": "Flipped [ready]→[active]: precondition met (main promoted via PR #1, base
    stable + green; ci-release-pipelines branch cut from it). Starting BUILD — author
    scripts/release.py + ci.yml + release.yml + justfile recipes, then dry-run validate.
    Cutting the first real release (task 7) deferred until the workflows land on main."
  "2026-09-09 (close)": "All tasks done → [done]. Merged via PR #2; workflows live on main. Task 7
    validated end-to-end by cutting v0.2.0, then v0.3.0 (the latter carrying the PR #3 CPU-only-torch
    CI fix). Reconciled during the 2026-09-09 reprioritization BUILD session (the merges + releases
    happened outside snap sessions). Awaiting the [active]→[done] git mv rename."
---

# CI + release pipelines (GitHub Actions + semver tagging)

## Executive Overview

Add GitHub Actions CI and release automation, adapted from the sibling-project sibling project's
templates captured at `_snap/reference/ci_content/` (`ci.yml`, `release.yml`, `release.py`).

- **CI** (`ci.yml`) — on push-to-`main` + PRs: `uv sync`, `ruff format --check`, `ruff check`,
  `ty check`. **No pytest in CI** — deliberate, matching the reference (PLAN 2026-09-08); tests
  stay a local/pre-commit responsibility for now.
- **Release** (`release.yml`) — on a `v*` tag: verify the tag equals `v$(uv version --short)`,
  then publish a GitHub Release with auto-generated notes (`softprops/action-gh-release`).
- **Bumper** (`scripts/release.py` + justfile `tag-patch|minor|major`) — bump → commit → tag →
  push via `uv version --bump`, so pushing the tag triggers `release.yml` and its version guard
  always passes.

Minutia's static `[project].version` under the hatchling build backend is exactly what
`uv version --bump` manages, so the reference `release.py` ports essentially as-is.

**This is a NEW feature, started AFTER `main` promotion.** `ci.yml` triggers on `main` and
`release.yml` on tags — neither is meaningful until `main` is the real trunk. Do not begin this
work on `uv_refactor`. Depends on `[ready]justfile-migration` (`ty` must already be wired, since
CI runs it).

**Non-goals**
- No PyPI publish (GitHub Release only for now).
- No tests-in-CI (deliberate; revisit as a follow-up if `main` needs a stronger gate).
- No doc rewrites — batched into the final stabilization doc pass.

## Task Checklist

- [x] **Precondition:** `main` is the real trunk (base promoted). Do not start otherwise.
      (Met 2026-09-09: `main` carries the stabilized base via PR #1; this branch cut from it.)
- [x] Add `scripts/release.py`, adapted from `_snap/reference/ci_content/release.py` (align the
      `chore: release <tag>` commit message with repo convention if desired; keep the dirty-tree
      and existing-tag guards and the `uv version --bump … --dry-run --short` preview).
- [x] Add `.github/workflows/ci.yml` (checkout, `astral-sh/setup-uv` with cache, `uv sync`,
      `ruff format --check`, `ruff check`, `ty check`).
- [x] Add `.github/workflows/release.yml` (`on: push tags v*`, `contents: write`, verify
      `v$(uv version --short) == GITHUB_REF_NAME`, `action-gh-release` with
      `generate_release_notes: true`).
- [x] Add justfile recipes `tag-patch` / `tag-minor` / `tag-major` →
      `uv run python scripts/release.py <level>`.
- [x] Dry-run validate: `uv run python scripts/release.py patch -n` previews the right tag and
      the guards fire on a dirty tree / pre-existing tag. (Validated 2026-09-09: previewed
      `v0.1.1`; both warnings fired — dirty tree + a throwaway `v0.1.1` tag, since deleted.)
- [x] Cut a first real release to validate end-to-end (tag pushes → `release.yml` publishes a
      Release with notes). Done 2026-09-09: `v0.2.0` cut (first release off the stabilized `main`,
      validated `release.yml`), then `v0.3.0` (carrying PR #3's CPU-only-torch CI fix). Both tags
      published; `pyproject` now `0.3.0`.

## Details

- **Reference files:** `_snap/reference/ci_content/{ci.yml,release.yml,release.py}` — copy and
  adapt, don't wholesale-import (the reference targets the sibling-project package and its `ty` layout).
- **Version source of truth:** `pyproject.toml` `[project].version` (hatchling, static). The
  `release.yml` guard reads it via `uv version --short`; `release.py` bumps it via
  `uv version --bump {patch|minor|major}`.
- **Why no tests in CI:** matches the reference and keeps CI fast; the value here is a green
  lint/type gate on `main` + reproducible tagged releases. Adding `pytest -m "unit or
  integration"` to `ci.yml` is a low-cost follow-up if desired later.
- **Dependency on `justfile-migration`:** CI runs `ty check`, so `ty` must already be a dev
  dependency and green. See `EXECUTIVE_SUMMARY.md` §4/§7 for the branch sequence.
