# Decisions

Append-only, culled log of what was done and why — the **past**. Read this to onboard. Each
entry: *what we set out to do / why / how it ended / why we stopped*. Newest first.

Session scratch lives in [`SESSION.md`](./SESSION.md); it is condensed into here at session
close.

---

## 2026-07-01: Unify `_blueprint` and `_snap` into a single AI-workspace system

- **What**: Migrated relevant content from the older `_blueprint/` workspace into `_snap/`
  (context docs, roadmap/decisions/feature-spec content); reset `_snap`'s core memory files,
  which had been seeded with leftover content from an unrelated project; removed the
  deprecated `conductor/` and `.gemini/` systems; deleted `_blueprint/` once its content was
  migrated or archived.
- **Why**: Three-plus overlapping AI-workspace systems (`_blueprint`, `_snap`, `conductor`,
  `.gemini`) had accumulated in the repo; consolidating on one ahead of an open-source release.
- **How it ended**: Completed. See `opensource_polishing.md` (repo root) for the parallel
  public-release audit that motivated this pass, including deferred items (notebook-output
  history scrub, vendored-SDK removal from git history).

## 2026-02-18: Production stability during refactor

- **What**: Created `notebooks/PRODUCTION_Summary_Generator.ipynb` as a frozen copy of the
  working notebook pipeline.
- **Why**: Allow continued production use of the known-good notebook workflow while the CLI
  and core libraries underwent refactoring and testing.
- **How it ended**: Notebook still in active use as of this writing; will be retired once
  `refactor_to_cli` reaches functional parity.

## 2026-02-18: Adopt `_blueprint/` structure (superseded 2026-07-01, see above)

- **What**: Centralized planning/context docs — previously loose `AGENTS.md`, `CLAUDE.md`,
  `TASKS-TODO.md`, and a `planning/` directory — into a new top-level `_blueprint/` directory.
- **Why**: Keep "source of truth" docs visible and separate from `src/`/`tests/`.
- **How it ended**: Superseded by the `_snap` system once a more structured PLAN/BUILD/ALIGN
  workflow was adopted (see the 2026-07-01 entry above).
