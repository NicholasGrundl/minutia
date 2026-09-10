---
state: active         # draft | ready | active | done | deprecated
changelog:
  "2026-09-09": "Initial spec — converged from an interactive PLAN session. Models the CLI on the
    sibling-project reference at _snap/reference/+cli_content/cli/. Prioritized FIRST, ahead of the
    refactor tail (eval-seams → orchestrator-retire-baseline)."
  "2026-09-09b": "Flipped [ready]→[active]; BUILD session begins on task 1 (scaffold the cli/
    package)."
  "2026-09-09c": "BUILD tasks 1-3 done (scaffold, cold-start, run group). Surface tweak (user
    decision): the full non-interactive pipeline is `run pipeline` (a leaf subcommand with a
    positional INPUT), not bare `run` — a Typer group cannot take a positional arg on its callback
    alongside subcommands. Bare `run` lists its subcommands."
---

# cli-wizard-redesign — CLI subpackage + rich first-run/guided wizard

## Executive Overview

Rebuild minutia's CLI from a flat 672-line `cli.py` into a clean `cli/` **subpackage** with a
concise top-level surface and a **full-screen rich wizard**, modeled on the sibling-project reference CLI
(`_snap/reference/+cli_content/cli/`). The bare `minutia` command becomes the opinionated daily
driver: it self-determines — run the guided pipeline, or walk a first-run setup wizard (persisting
the API key + recordings dir) when unconfigured, then run. Power-user execution moves under a `run`
group; read-only introspection under an `info` group.

**Why:** the base is stable and released (v0.3.0); the CLI is now the primary interface and the
place the tool is actually used. The current CLI works but is a single ad-hoc module: two divergent
one-shot paths (`go` wizard vs `process-all`), inline `typer.prompt` menus, and heavy imports
(torch/whisper) that fire on *every* invocation — even `--help` and `config`. This feature makes the
CLI the polished, opinionated front door: fast cold start, a real wizard, easy notes entry, and
persisted setup so the tool is ready after first run.

**The workflow this optimizes for** (user's stated daily loop):
1. Drop new recordings into a recordings dir.
2. Run often, summarizing against notes — pasted as full text **or** a file (the highest-frequency
   action → a first-class notes panel).
3. After outputs are created, manually remove the mkv + outputs and archive them per project (so the
   run **ends with a clear artifacts summary + a nudge to clean up manually** — no archive command).

**Non-goals (explicitly deferred):**
- **`resume` / re-run / summarize-as-jobs** — the re-run and evaluation flows belong to
  `eval-seams` / `evals-harness`, updated later.
- **Archive/cleanup command** — end-of-run is a message only; archiving (and any "project" concept)
  is a separate future feature.
- **Engine unification / orchestrator** — `process-all` + `PipelineOrchestrator` leave the CLI
  surface but the code stays in the repo, unused, retired later by `orchestrator-retire-baseline`.
  This feature does not invest in the legacy engine.
- **OS keyring** — the API key is stored in plaintext `config.env` (chmod 600), not a secret store.
- **Env-file-path key method** — only *paste* and *detect-from-env* ship now (see Details); a
  future env-file method would copy the key out, not store a pointer.
- **A `personal_info` wizard panel** — stays config-driven as today.

## Task Checklist

- [x] **Scaffold the `cli/` package.** Done as a **minimal move** (user decision): `cli/app.py`
      (all current commands, via `git mv`) + `cli/_steps.py` (shared step helpers) + `cli/__init__.py`
      re-exporting **`main` only** — re-exporting the Typer `app` would shadow the `app` submodule and
      break module-level test patching (the Typer lives at `cli.app.app`). `run`/`setup`/`info`/
      `wizard` modules are created by their own later tasks, not up front. Tests retargeted to the new
      module paths; gate green.
- [x] **Cold-start discipline.** Heavy step imports made lazy inside the `cli/_steps.py` functions.
      **Root cause was `src/minutia/__init__.py`** eagerly importing the whole heavy stack (any
      `minutia.X` import pulled torch/whisper/anthropic) — slimmed to light imports + PEP 562
      `__getattr__` lazy step modules (back-compat preserved). Added eager `--version` callback.
      Subprocess regression test (`tests/unit/test_cli_cold_start.py`): `--version`/`--help`/`config`
      import none of torch/whisper/anthropic. (Note: `info`/`setup` from the spec don't exist yet —
      Tasks 4 & 7 — so the cheap surfaces tested today are `--version`/`--help`/`config`.)
- [x] **`run` command group.** `minutia run pipeline` runs the whole pipeline non-interactively on
      the shared step helpers (`run_full_pipeline` in `cli/_steps.py`, off the orchestrator); `run
      extract-audio | transcribe | merge | summarize` are the migrated step commands; bare `run`
      lists them. Removed `go` and `process-all` from the CLI surface. Cost gate mirrors `summarize`
      (prompt / `--yes` / `--dry-run`). Regression tests ported; gate green (ruff + ty + 98 pytest).
- [x] **`info` group.** `cli/info.py`: bare `minutia info` prints resolved settings + provenance
      (config-display moved verbatim from `app.py`); `info config` aliases it; `info recordings`
      lists the newest `.mkv` in the recordings dir (friendly errors: no dir configured / dir
      missing; caps at 10 + "… and N more"). TDD'd the pure `_list_recordings`. **Top-level `config`
      removed.** Gate green (ruff + ty + 105 pytest); cold start still clean.
- [ ] **Config persistence writer.** A pure function that writes/merges the user `config.env`
      (platformdirs), preserving existing keys and `chmod 600` (it now holds a secret). Used to
      persist `recordings_dir` + the API key. TDD: round-trips, preserves unrelated keys, idempotent
      re-write, correct permissions, never logs the key.
- [ ] **`wizard/tui.py` — full-screen chrome.** Port the reference's rich primitives: persistent
      header, `select` menu (highlighted row styled), inline text/paste field, a **multi-line notes
      field** (Enter = newline, Ctrl-D submits), and a **staged progress bar**. Footer shows the
      keystroke hints on every screen. Keys via `yakh`; drawing via `rich` on the alternate screen.
      Injectable render + key source so tests drive it without a real terminal. Adds `rich` + `yakh`.
- [ ] **`wizard/flow.py` — flows + pure cores.** (a) **Setup flow**: recordings-dir panel +
      API-key panel (paste / detect-from-env → persist via the writer). (b) **Guided-run flow**: pick
      recording (newest-first) → prompt-kind menu → **notes panel** (multi-line paste / pick a file /
      none) → cost confirm → staged pipeline (extract → transcribe → merge → summarize) → **artifacts
      summary + manual-cleanup nudge**. Split the pure cores (resolve/persist/plan) from the TUI. TDD
      the cores; test the flows with an injected TUI + mocked steps.
- [ ] **Bare `minutia` self-determination.** `app.py` callback (`invoke_without_command=True`):
      resolve settings; if API key + recordings dir resolve → guided-run flow; else → setup flow →
      then guided-run. `minutia setup` runs the setup flow unconditionally. Tests: bare routes to
      run vs setup based on resolution (mocked).
- [ ] **Docs + gate.** Rewrite the CLI sections of `README.md` + `AGENTS.md` for the new tree
      (`run`/`setup`/`info`, bare wizard, `go`/`process-all` removed); note the new `rich`/`yakh`
      deps and the persisted-key behavior. Full gate green (ruff + ty + pytest); retire/replace the
      `go` + `process-all` tests.

## Details

### Reference

Model: `_snap/reference/+cli_content/cli/` (the sibling-project CLI). Patterns to mirror:
- **Thin `app.py`** that only *wires* (`app.command(...)(fn)`, `app.add_typer(sub, name=...)`).
- **Self-determining bare command** (`invoke_without_command=True` + a callback that dispatches when
  no subcommand is given).
- **Cold-start discipline** — heavy imports live behind dispatch; `--version`/`--help` stay cheap.
- **Wizard split** — `flow.py` (flow + *pure*, directly-unit-tested cores) vs `tui.py` (all drawing;
  injectable `render`/`sleep`/keys for tests). See its `select`, `prompt_path`, `Step`,
  `run_staged_progress`.
- **Pure resolution vs side-effecting primitive** (`resolve_serve_plan` → `ServePlan` dataclass,
  separate from `serve_app`) — minutia's analog is a `RunPlan` dataclass resolved before execution.
- **Actionable errors** that name the exact next command.
- **Read-only `info` group** that works on a fresh machine; needy subcommands fail fast.

### Final command tree

```
minutia                 wizard — interactive daily driver (self-determines)
minutia run             lists the run subcommands (help)
minutia run pipeline    run the whole pipeline (non-interactive); positional INPUT
minutia run extract-audio | transcribe | merge | summarize   one step
minutia setup           config wizard (recordings dir + API key), unconditional
minutia info            resolved settings + provenance
minutia info config     alias of bare info
minutia info recordings list newest .mkv in the recordings dir
```
`go` and `process-all` are removed (`run pipeline` + the step subcommands supersede both).
`--version` is a top-level eager option.

**Why `run pipeline` and not bare `run`** (build-time decision, 2026-09-09): a Typer group cannot
take a *positional* `input_video` on its callback while also exposing subcommands — click cannot
disambiguate `run extract-audio` (subcommand) from `run file.mkv` (positional). Making the full run
its own leaf subcommand (`run pipeline`) restores the positional-`INPUT` ergonomics of the old
`process-all` and keeps `run <step>` unambiguous. Bare `run` shows help.

### Bare `minutia` flow (the daily driver)

1. Resolve settings. If API key **and** recordings dir resolve → skip to step 4.
2. **Setup — recordings-dir panel** (if unset): confirm/enter the dir → persist.
3. **Setup — API-key panel** (if unresolved): choose input method → persist.
4. **Pick recording** — newest-first menu of `.mkv` in the recordings dir.
5. **Prompt-kind** menu.
6. **Notes panel** — multi-line paste (Enter = newline, Ctrl-D submits) **or** pick a file **or**
   none; keystroke hints in the footer.
7. **Cost confirm** → staged progress bar over extract → transcribe → merge → summarize.
8. **Artifacts summary** — list every artifact created + its path (report, merged transcript, audio,
   output dir), then a one-line nudge to remove the mkv + outputs / archive per project manually.

### Persistence model

- **Home:** the existing user config file (platformdirs `config.env`), read by the
  `settings-resolution` layer with correct precedence (CLI > env > contextual `.env` > user config >
  default). The wizard becomes its **writer**.
- **Writer:** pure, merges into the existing file (preserves unrelated keys), sets `chmod 600`, never
  echoes/logs the key value.
- **Persisted:** `MINUTIA_RECORDINGS_DIR`, the API key
  (`MINUTIA_ANTHROPIC_API_KEY`/`ANTHROPIC_API_KEY` — match the settings layer's expected var), and
  optionally default prompt-kind / output dir.
- **API-key input methods (ship two):**
  1. **Paste the key** — a field to paste `sk-ant-…`; written to `config.env`.
  2. **Use an env var already set** — detect `ANTHROPIC_API_KEY` / `MINUTIA_ANTHROPIC_API_KEY` in the
     environment; offer to use as-is (env-only) or persist a copy.
  - *(Deferred)* point-to-an-env-file: if added later, it **copies the key out** into `config.env`
    (no stored pointer).

### Wizard TUI (`wizard/tui.py`)

Hand-rolled rich full-screen chrome on the alternate screen (persistent header that never scrolls),
ported from the reference. Primitives: `select` (single-select menu), a text/paste field, a
**multi-line notes field** (the one addition over the reference — Enter inserts a newline, Ctrl-D
submits, handles multi-line paste), and the staged progress bar (`Step` + `run_staged_progress`).
Keys via `yakh` (`python-yakh`); no web/heavy imports so bare dispatch stays cold-start cheap. A
footer shows keystroke hints on every screen (`↑/↓ move · Enter … · Esc …` style; the notes field's
own hint). Render and key source are **injectable** so tests assert flow/ordering without a TTY (as
the reference injects `render`/`sleep`).

### Package layout

```
src/minutia/cli/
  __init__.py     # re-export app, main  (keeps minutia.cli:main + CliRunner imports working)
  app.py          # Typer app wiring + bare self-determining callback + --version
  run.py          # `run` group: run-all + the four step subcommands
  setup.py        # `setup` command → wizard.flow setup flow
  info.py         # `info` group: settings/provenance, config alias, recordings
  wizard/
    __init__.py   # public surface: run_guided(), run_setup()
    flow.py       # flows + pure cores (resolve, persist, RunPlan)
    tui.py        # rich full-screen chrome (rich + yakh), injectable render/keys
```

### Engine

`minutia run` (all) and the guided-run flow both execute on the **shared step helpers** (the current
`_extract_audio_step` / `_transcribe_step` / `_summarize_step`, migrated into the package — likely a
`cli/_steps.py` or reused from `steps/`). `PipelineOrchestrator` + `baseline_pipeline.py` are **not**
used by the new CLI; they stay in the repo untouched and are retired by
`orchestrator-retire-baseline`. No engine unification here (deliberate — legacy is lowest priority).

### New dependencies

- `rich` — full-screen rendering (add explicitly; currently only pulled transitively via typer).
- `yakh` (dist `python-yakh`) — cross-platform keystroke reading.
- (torch/whisper/anthropic already present.)

### Testing approach (per BUILD methodology)

- **TDD (pure logic):** config-persistence writer, recordings listing, settings/resolution helpers,
  the `RunPlan` resolver, notes/path resolution.
- **Injected-render unit tests (TUI):** drive `select` / fields / progress with a scripted key
  source + recording renderer; assert screens, selections, and step ordering — no real terminal.
- **Integration (guided run):** end-to-end flow with an injected TUI + **mocked** whisper and
  **mocked** Anthropic (never a real call), asserting the pipeline runs and the artifacts summary is
  produced. Reuse existing fixture scenarios where possible.
- **Cold-start test:** assert `torch` is not imported for `info` / `--help` (subprocess or an
  import tracker).

### Priority

Prioritized **first**, ahead of the refactor tail (`eval-seams` → `orchestrator-retire-baseline`),
per the user (2026-09-09): the CLI is where the tool is used, and restructuring it now makes the
later features easier to design against.

### Open items to confirm at build time

- Exact key env-var name to persist (align with what `settings-resolution` reads as the winning
  API-key source).
- Whether `minutia run` (all) reuses the migrated step helpers directly or a small shared runner
  module — decide during task 3, keep it off the orchestrator.
