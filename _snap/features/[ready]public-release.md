---
state: ready
changelog:
  "2026-11-11 12h": "Initial spec — converged from interactive planning session."
---

# public-release

## Executive Overview

**What:** finish preparing the `public-cleanup` branch, fast-forward `main` to it, publish the
release history, and flip the GitHub repo to public.

**Why:** minutia is going public as a portfolio project. It should look like what it is: a real,
working tool with a real history that keeps being improved in the open. So the bar for launch is
"honest and tidy", not "finished". Larger cleanups are deliberately left for visible work after
launch.

**Non-goals** (each was considered and deferred on purpose):

- No further history rewriting. The rewritten history stays as it is.
- No dead-code removal. `baseline_pipeline.py`, `pipeline/orchestrator.py`, `legacy/` and
  `clients/` stay; the existing `orchestrator-retire-baseline` and `eval-seams` specs own them.
- No fixture changes. All four `tests/fixtures/scenarios/` stay in HEAD; the test suite and
  fixtures get their own sprint after launch (see BACKLOG).
- No summarizer rework. Typing, the unknown-model bug and the tokenizer wait for `eval-seams`.
- No README screenshot or GIF at launch; it is the first follow-up after going public.
- No PyPI publish.
- No AI workflow files in git: `.claude/`, `.agents/`, `_snap/skills/`, `_snap/prompts/`,
  `_snap/context/` and `_snap/reference/` are local-only.

**Working mode for BUILD sessions:** one or two steps per response. The user runs every git and
GitHub command; the agent says what to run and what to check, and edits files only.

## Task Checklist

All work happens on `public-cleanup` as normal commits, one task per commit unless noted.

### Stage A — snap workspace is local-only

- [ ] **A1. Ignore and untrack the private paths.** Add `/_snap/reference/`, `/_snap/context/`,
      `/_snap/skills/`, `/_snap/prompts/`, `/.claude/`, `/.agents/` and `*:Zone.Identifier` to
      `.gitignore`. Untrack the two tracked reference notes with `git rm --cached` (files stay on
      disk). `_snap/archive/` stays tracked. *Check:* `git ls-files` lists nothing under those
      paths; `git status` no longer shows the handoff notes.
- [ ] **A2. Restore local-only content.** Only after A1 is committed, copy skills, prompts,
      context, reference and the agent skill dirs from the private archive clone into the ignored
      paths, skipping `*:Zone.Identifier` files. *Check:* `git status` is clean; the PLAN / BUILD /
      ALIGN playbooks are readable under `_snap/prompts/`.
- [ ] **A3. Fix public-facing snap docs.** In `_snap/ROADMAP.md`: repoint the
      `../EXECUTIVE_SUMMARY.md` link to `./archive/EXECUTIVE_SUMMARY.md`, drop the
      `+planning/opensource_polishing.md` reference, and reword the dogfooding section so it does
      not link into `reference/`. Confirm `_snap/AGENTS.md` says which folders are local-only.
      *Check:* every relative link in tracked `_snap/*.md` resolves to a tracked file.

### Stage B — polish

- [ ] **B1. Add `LICENSE`** (MIT, matching `pyproject.toml`).
- [ ] **B2. Track `.python-version`** (`3.12`). Remove the `.python-version` line from
      `.gitignore` so it can be committed. *Check:* a fresh clone's `uv sync` picks 3.12 without
      a `--python` flag.
- [ ] **B3. README install section.** Remove the "only while the repo is private" auth step from
      `README.md` and the matching private-repo section in `docs/setup.md`. The legacy
      baseline-pipeline section stays, since that code stays.
- [ ] **B4. Refresh root `AGENTS.md`.** `make` targets → `just` recipes; drop the "mid-refactor"
      status and the notebook-fallback wording; fix links to archived specs; `minutia config` →
      `minutia info`; mypy → ty; remove the broken `make commit` note. *Check:* every command
      shown exists in the `justfile` or the CLI; every relative link resolves.
- [ ] **B5. Remove unused dependencies** `nanoid`, `transformers`, `instructor`, `openai` from
      `pyproject.toml` and relock. `scipy`, `sounddevice` and `numpy` stay (used by `legacy/`).
      *Check:* `just test` passes; `uv run minutia --help` works.
- [ ] **B6. CI runs the unit tier.** Add `uv run --extra cpu pytest -m unit` to
      `.github/workflows/ci.yml` after lint and ty, and update the "No pytest in CI" comment.
      *Check:* the workflow is green on the pushed branch.
- [ ] **B7. Fix prompt typos** in `src/minutia/steps/summarize_transcript.py`. Text only; no
      behavior or signature changes.
- [ ] **B8. `minutia info` trailing newline.** The first log line prints without a newline.
      TDD: a failing unit test on the captured output first, then the fix.

### Stage C — go public

- [ ] **C1. Privacy sweep of the final tree.** Grep tracked files for client and company names,
      home-directory paths, email addresses, API-key shapes and meeting content. The user supplies
      the name list at build time; it is never written into a tracked file. *Check:* zero hits, or
      each hit reviewed and accepted by the user.
- [ ] **C2. Fast-forward `main`** to `public-cleanup` and push. *Check:* CI green on `main`.
- [ ] **C3. Recreate and push the old tags** `v0.2.0`, `v0.3.0`, `v0.4.0` on their
      `chore: release vX.Y.Z` commits. Push one at a time. *Check:* three GitHub releases exist
      and each release run passed its tag-equals-pyproject guard.
- [ ] **C4. Cut `v0.4.1`** with `scripts/release.py` so the newest release matches the polished
      `main`. *Check:* release run green; `pyproject.toml` reads `0.4.1`.
- [ ] **C5. Inspect on GitHub, then flip to public.** Review the rendered README, file tree,
      releases, Actions history and branch list while still private; delete `public-cleanup` on
      the remote once merged; then change visibility.
- [ ] **C6. Verify the public install.** From an environment with no GitHub credentials:
      `uv tool install git+https://github.com/NicholasGrundl/minutia@main`, then `minutia --version`
      and `just reinstall`. *Check:* both succeed and report `0.4.1`.

**Done when:** the repo is public, `main` is green, four releases are listed, and an
unauthenticated install works.

## Details

### Starting state (2026-11-11)

- `public-cleanup` = `main` + the bedrock-summarizer commit + one commit that pruned `_snap/` to
  the project record. That prune already removed `_snap/context/` and reworded `_snap/AGENTS.md`
  and the root `AGENTS.md` to say the skills and playbooks are kept privately. That wording is
  correct and stays.
- `main` has not received either commit yet. No tags exist in the rewritten repo.
- A local-only handoff note pair in `_snap/reference/` records the private paths (archive clone,
  backups). BUILD sessions read those for paths; nothing from them is copied into tracked files.

### Decisions taken in planning

- **AI workflow files stay private.** An interim plan to commit the snap skills and playbooks
  was considered and rejected. The repo shows the *output* of the system (ROADMAP, DECISIONS,
  feature specs), not the tooling.
- **`_snap/archive/` stays tracked.** It holds the six completed feature specs plus the
  stabilization brief, which ROADMAP and `tests/README.md` link to. Keeping it means no file
  moves and no dead links. `_snap/reference/` becomes local-only because it is a scratch
  dumping ground.
- **Dead code stays for launch.** Removing the orchestrator and baseline pipeline touches
  `tests/conftest.py`, three test modules and a shared mock, and the roadmap already sequences
  that work behind `eval-seams`. Doing it in public afterwards is the point.
- **Fixtures stay for launch.** Replacing them is folded into a later test-suite sprint that
  builds benchmark-style fixtures for evals.
- **Summarizer: typos only.** `eval-seams` restructures that module; the token estimate
  (currently a GPT tokenizer applied to Claude) and the unknown-model lookup bug in ROADMAP
  "Known issues" are fixed there.
- **Releases: old tags plus `v0.4.1`.** Shows the real release cadence and leaves the latest
  release equal to the public HEAD.

### Notes per task

- **A1 ordering matters.** The ignore rules must be committed before A2 copies anything in,
  otherwise private files show up as untracked and can be added by accident.
- **A1 and `/+*/`.** `.gitignore` already ignores `+`-prefixed working folders and
  `/_snap/reference/+*/`; the latter becomes redundant once `/_snap/reference/` is ignored and
  can be removed in the same commit.
- **B2.** `.python-version` is currently ignored by the stock Python `.gitignore` block (the
  "pyenv" entry). `requires-python` is already `>=3.12,<3.14`; the pin exists because the locked
  torch wheels are cp312-only, so a 3.13 interpreter fails at sync.
- **B5.** Removing `openai` does not affect `openai-whisper`, which is a separate package.
  `tiktoken` stays; the summarizer imports it.
- **B6.** CI already syncs with `--extra cpu`, so the unit tier needs no new install step. The
  original choice to keep pytest out of CI is recorded in the archived `ci-release-pipelines`
  spec; this task reverses it for the unit tier only. Integration and slow tiers stay local.
- **C3 tag mapping.** Find each commit with `git log --oneline --grep="chore: release v"`. On
  the rewritten history these are `4df29f8` (v0.2.0), `786bef5` (v0.3.0) and `d4f096b`
  (v0.4.0); re-check before tagging. The release workflow only runs for a tag whose commit
  contains `.github/workflows/release.yml`, and its guard compares the tag to that commit's
  `pyproject.toml` version. If an old tag's commit predates the workflow, no release is created
  for it; create that release by hand from the tag or accept the tag without a release.
- **C4.** `scripts/release.py` bumps the version, commits, then tags, in that order. Run it
  from `main` after C2.
- **C5.** Tags and releases are created while the repo is still private, so a failed release
  run can be fixed before anyone sees it.

### Testing approach

- B8 is TDD (unit test on captured CLI output).
- B5 and B6 are verified by the existing suite: `just test` locally, the new unit step in CI.
- A1–A3, B1–B4, B7 are file and doc changes verified by the checks listed on each task.
- Stage C is verified by observation on GitHub and by the unauthenticated install in C6.

### Standing rule

Anything written to tracked `_snap` files (ROADMAP, DECISIONS, SESSION, `features/`,
`archive/`) is public. No client names, meeting details or private paths there.

### After launch (not tasks of this spec)

- README screenshot or GIF of the wizard.
- Test-suite and fixtures sprint (BACKLOG): benchmark-style fixtures, synthetic-data
  primitives, evals living inside the test suite.
- `eval-seams`, then `orchestrator-retire-baseline`, as already ordered in the ROADMAP.
- PyPI publish (on hold).
