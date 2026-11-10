# Archive Log

Append-only record of everything moved into `archive/`. Files keep their original names; this log
explains what and why. Newest first.

Each entry: `YYYY-MM-DD` · `path(s)` · short why.

---

**2026-11-10** · `skills/`, `prompts/`, `context/`, `archive/blueprint/`, `archive/old_claude_stuff/`,
`reference/ci_content/` (plus the activated copies in `.claude/skills/` and `.agents/skills/`)
→ removed from this repo, not archived here · Public-release prune. The playbooks and skills are
the reusable workflow and live in a private repo; `context/` was cached third-party documentation;
the blueprint and old-command archives were superseded planning material. The project-specific
record stays: `ROADMAP.md`, `DECISIONS.md`, `features/`, `archive/features/`.

**2026-09-09** · `features/[done]{ci-release-pipelines,finish-cli-parity,justfile-migration,refactor_to_cli,settings-resolution,tests-refactor}.md`
→ `archive/features/` · The stabilization arc is complete and shipped (base on `main`, CI +
releases live, `v0.3.0` out). Archived all six `[done]` specs to keep `features/` scoped to live
work (`[ready]`/`[draft]`) during the post-stabilization reprioritization. `ci-release-pipelines`
was flipped `[active]→[done]` first (its own move). History/narrative for all six lives in
[`DECISIONS.md`](../DECISIONS.md); `ROADMAP.md` §Done keeps a condensed summary with links
repointed here. Files keep their `[done]` names.

**2026-07-01** · `blueprint/` (whole tree, formerly repo-root `_blueprint/`) · Unifying onto
`_snap` as the single AI-workspace system ahead of open-source release. Content that was still
live/useful was migrated first (see [`DECISIONS.md`](../DECISIONS.md) 2026-07-01 entry):
context docs (`ffmpeg`, `claude`, `anthropic`, `whisper`) moved to `_snap/context/`; roadmap,
issues, and decisions folded into `_snap/ROADMAP.md` / `DECISIONS.md`; the design + refactor
planning docs consolidated into `_snap/features/[active]refactor_to_cli.md`. What's archived
here is the original raw material plus items with no further live purpose: design-feedback
transcripts, the old test audit, `conda_packages.txt`, superseded planning drafts, the old
`PROMPT-*` playbooks (superseded by `_snap/prompts/`), the `smart-tree` skill (superseded by
`_snap/skills/snap-search`), and `_blueprint/AGENTS.md` itself. Deliberately **not** archived:
duplicate `context/claude copy/` (already deleted), context topics that duplicated existing
`_snap/context/` folders (`agent-skills`, `gemini-cli`, `platformdirs`, `pytest`,
`pytest-mock`, `rapidfuzz`, `ruff`, `ty` — no unique content), and the vendored
`anthropic`/`whisper` SDK `repo/` clones (not Minutia's code; still present in git history
until the deferred `git-filter-repo` pass noted in `opensource_polishing.md`).
