---
state: ready          # draft | ready | active | done | deprecated
changelog:
  "2026-09-08": "Initial spec — the release/CI half of the tooling modernization. Blocked by
    main promotion; started as a fresh feature once main is the real trunk. Sibling of
    [ready]justfile-migration."
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

- [ ] **Precondition:** `main` is the real trunk (base promoted). Do not start otherwise.
- [ ] Add `scripts/release.py`, adapted from `_snap/reference/ci_content/release.py` (align the
      `chore: release <tag>` commit message with repo convention if desired; keep the dirty-tree
      and existing-tag guards and the `uv version --bump … --dry-run --short` preview).
- [ ] Add `.github/workflows/ci.yml` (checkout, `astral-sh/setup-uv` with cache, `uv sync`,
      `ruff format --check`, `ruff check`, `ty check`).
- [ ] Add `.github/workflows/release.yml` (`on: push tags v*`, `contents: write`, verify
      `v$(uv version --short) == GITHUB_REF_NAME`, `action-gh-release` with
      `generate_release_notes: true`).
- [ ] Add justfile recipes `tag-patch` / `tag-minor` / `tag-major` →
      `uv run python scripts/release.py <level>`.
- [ ] Dry-run validate: `uv run python scripts/release.py patch -n` previews the right tag and
      the guards fire on a dirty tree / pre-existing tag.
- [ ] Cut a first real release to validate end-to-end (tag pushes → `release.yml` publishes a
      Release with notes). Likely `v0.2.0` (first release off the stabilized `main`).

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
