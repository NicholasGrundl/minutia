# `_snap` — AI Development Workspace

`_snap` is the per-project workspace I use for AI-assisted development. It holds the project's
cross-session memory and feature specs as plain files, so project state is visible and reviewable
rather than living in an opaque AI memory.

This public copy carries the **project-specific record** for minutia: the roadmap, the decision
log, and the feature specs. The session playbooks and skills that drive the workflow are kept in
a private repo.

> This file is the **single source of truth** for how `_snap` is organized here. `CLAUDE.md` is a
> pointer to it.

## Filetree

```
_snap/
  AGENTS.md          # this file — overview + conventions
  ROADMAP.md         # FUTURE  — ordered list of features to build
  SESSION.md         # PRESENT — ephemeral session scratchpad (flushed at close)
  DECISIONS.md       # PAST    — append-only decision log + history (read this to onboard)
  features/          # feature specs <name>.md + conventions               (+ AGENTS.md)
    BACKLOG.md       #   unscheduled feature ideas
  reference/         # working notes (research write-ups, dogfooding log)
  archive/           # ARCHIVE.md (append-only log) + completed feature specs
```

## Cross-session memory — future / present / past

The three core files are the same system at different zoom levels:

- **`ROADMAP.md`** — *future*: ordered features to build; "phases" are ephemeral grouping labels only.
- **`SESSION.md`** — *present*: the current session's working scratchpad — sub-tasks, in-flight
  reasoning. Wiped at flush.
- **`DECISIONS.md`** — *past*: append-only, culled log — *what we set out to do / why / how it
  ended / why we stopped*.

## The work lifecycle

```
PLAN   idea ─interview→ features/<name>.md  [draft]→[ready];  add it to ROADMAP
BUILD  [ready]→[active]; pick a task ─just-in-time→ sub-tasks in SESSION.md; commit as you go
       CLOSE → flush SESSION ─condense→ DECISIONS; tick task checkboxes; bump ROADMAP
ALIGN  reconcile ROADMAP / features / SESSION / DECISIONS vs reality
```

**Tiers:** *Feature* is the unit of work (a doc in `features/`). *Tasks* are its concrete,
testable checklist items. *Sub-tasks* are session-level steps, decomposed just-in-time into
`SESSION.md` — never pre-listed. *Phases* are only sequencing labels in `ROADMAP.md`.

## The git axis (separate from the memory files)

Git carries **file-level change intelligence**, orthogonal to the memory files:
- **micro commits** — per-file change detail (the `[MICRO]` commits in older history).
- **macro commits** — human-readable `[MACRO]` checkpoints at task/feature boundaries
  (≈ a DECISIONS entry). `git log --grep '\[MACRO\]'` lists them.

## Conventions

- **Moves are sacred:** every `mv`/`git mv` is a **separate, individually-approved** operation,
  committed on its own — never bundled with content edits.
- **Rules:** `AGENTS.md` is canonical in every folder that has rules; `CLAUDE.md` points to it.
- **Archive:** never silently delete history — append an entry to `archive/ARCHIVE.md`
  (timestamp + path(s) + why); files keep their names.
- **Features:** see `features/AGENTS.md` — frontmatter state, doc structure, naming.
- **Formatting:** avoid wide markdown tables (they don't wrap in narrow windows) — prefer
  list/section layouts.
