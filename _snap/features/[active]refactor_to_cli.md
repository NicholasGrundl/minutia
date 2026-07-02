---
state: active
changelog:
  "2026-07-01 15h": "created by consolidating _blueprint architecture/testing docs + REFACTOR_ACTION_PLAN, cross-checked against actual src/ state"
  "2026-07-02 PLAN": "re-planned against the real daily workflow (SummaryPromptVariations.ipynb): parity target changed from baseline_pipeline.py to the notebook driver; 'Soul' phase replaced by prompt-kind + per-meeting context files; added low-surface eval seams (SummaryClient protocol, run-metadata sidecar, enumerable prompt registry); orchestrator hardening resequenced after CLI parity"
  "2026-07-02 PLAN(2)": "added CLI Foundations phase: click→typer migration; platformdirs-backed defaults (output home ~/Documents/minutia, user-global config, recordings dir + latest-MKV input discovery); light interactive mode in parity phase; full guided TUI deferred to BACKLOG"
---

# Refactor to Production CLI (v0.2.0)

## Executive Overview

Minutia is transitioning from a notebook-driven workflow into a proper `src/minutia/` package:
`RunPaths`-based path management, a `PipelineOrchestrator`, one module per pipeline stage under
`steps/`, and a **typer** CLI (migrating off Click — Phase 3). Testing follows a "Golden
Sample" methodology — fixtures with
known-good outputs generated from the trusted legacy notebook live in
`tests/fixtures/scenarios/`, and refactored logic is validated against them.

**Parity target (updated 2026-07-02)**: the reference workflow is
`notebooks/SummaryPromptVariations.ipynb` — the user's actual daily driver — **not**
`baseline_pipeline.py` or `CreateTranscriptProd.ipynb`. Crucially, that notebook already
imports and runs the refactored `minutia.steps.*` modules; the remaining gap is the *driver*
layer (prompt-kind selection, per-meeting context, cost preview, markdown report, idempotent
re-runs), not the pipeline logic. **The milestone that matters: `minutia summarize` (and the
step commands) fully replace the notebook for daily use.**

This spec also cuts two cheap seams for the future evals harness (comparing summarization
LLMs/prompts and transcription approaches — see the opensource_portfolio draft): a provider
client protocol in `clients/` and a run-metadata sidecar. Seams only — no eval harness here.

**Non-goals** (for this spec): rich CLI progress UI, resume-from-failure beyond
skip-if-exists, local LLM summarization (the seam lands, the Ollama client doesn't), the evals
harness itself, SQL-backed job tracking. Those belong to the broader post-refactor vision —
see [`[draft]refactor_for_opensource_portfolio.md`](./%5Bdraft%5Drefactor_for_opensource_portfolio.md).

## Task Checklist

### Phase 0: Foundation (golden samples) — DONE
- [x] Generate golden-sample fixtures for `microphone_only`, `noisy_microphone`,
      `podcast_desktop`, `youtube_desktop` scenarios (`tests/fixtures/scenarios/`)

### Phase 1: Plumbing & Cleanup — DONE
- [x] Fix package entry point (`minutia = "minutia.cli:main"`; `__init__.py` exports `steps`,
      `pipeline`, `clients`, `config`, `logging`, `paths`, `run_metadata`)
- [x] Isolate legacy Jupyter-era code into `src/minutia/legacy/`
      (`ui_jupyter.py`, `claude_audio_widget.py`, `gpt_audio_widget.py`)
- [x] Reorganize tests into `tests/{unit,integration,slow,fixtures,mocks,scripts}/`

### Phase 2: Logic Unification — DONE (2026-07-02)
- [x] Port `generate_long_summary` (token-continuation loop) into
      `src/minutia/steps/summarize_transcript.py`
- [x] Consolidate `prompts.py` as the single prompt registry: add the three builders that
      exist only in `SummaryPromptVariations.ipynb` (`slide-review`, `interview-debrief`,
      `discovery-summary`), plus `get_prompt_builder(kind)` and `list_prompt_kinds()`
      (TDD — unit tests assert every kind renders with/without notes and personal info)
      *(2026-07-02: done; unknown kind now raises ValueError, tests in
      `tests/unit/test_prompts.py`)*
- [x] Point `SummaryPromptVariations.ipynb` at `minutia.prompts` (delete its inline builder
      cells) — proves registry parity while the notebook is still the daily driver
      *(2026-07-02: done; 6 builder cells deleted, dispatcher + filename prompt now imported;
      `extract_transcript_text`/`get_filename_from_content`/`create_markdown_report` stay
      notebook-local until the next task moves them into `steps/`)*
- [x] Move `get_filename_from_content` + `create_markdown_report` from
      `baseline_pipeline.py` into `steps/summarize_transcript.py` (move, not rewrite; the
      notebook's third copy dies when the CLI replaces it)
      *(2026-07-02: done; baseline re-exports from the step; notebook imports from the step
      too — its local copies removed early; stale default model fixed to claude-sonnet-4-6;
      4 unit tests in `tests/unit/steps/test_summarize_transcript.py`)*
- [x] Verify merger step (`transcript_merger.py`) against `03_merged/` golden fixtures
      *(2026-07-02: verified — all 4 scenarios reproduce their goldens exactly; frozen as
      `test_merger_reproduces_golden_fixture` in `tests/integration/test_transcript_merger.py`)*

### Phase 3: CLI Foundations (typer + paths/config defaults) — NOT STARTED
- [ ] Port the five existing commands from Click to **typer** 1:1 — no behavior change
      (typed params, enum choices, `typer.Context` for the shared config object); swap
      `click` → `typer` in `pyproject.toml`; existing CLI tests keep passing
- [ ] Add **platformdirs** dependency; `config.py` gains:
      `recordings_dir` (`MINUTIA_RECORDINGS_DIR`; where OBS drops MKVs, no default),
      `base_output_dir` default changes `./runs` → `platformdirs.user_documents_path()/
      "minutia"`, and a `personal_info_path` default
- [ ] User-global config file at `platformdirs.user_config_path("minutia")/config.env`,
      loaded *after* CWD `.env`/`.minutia` (which keep winning for project-local dev);
      full precedence: CLI flag > env var > CWD `.env` > user config > platformdirs default
- [ ] Input-resolution helper (`paths.py` or `cli.py`): explicit MKV path wins; else the
      **newest `.mkv` in `recordings_dir`** (always echo which file was picked); actionable
      error if `recordings_dir` is unset or empty (TDD — unit tests over the precedence
      chain with tmp dirs)
- [ ] `minutia config` command: print resolved config values and their sources (which file/
      env/default each came from) — cheap, and de-mystifies the precedence chain

### Phase 4: CLI Parity with `SummaryPromptVariations.ipynb` — NOT STARTED
- [ ] `summarize` command upgrade (`cli.py`): `--prompt-kind` (choices from
      `list_prompt_kinds()`), `--notes FILE`, `--personal-info FILE` (both optional, both
      defaultable from config), route through `generate_long_summary(system_prompt=...)`,
      write markdown report via `create_markdown_report` (Tracer-Bullet, then unit tests
      with mocked Anthropic)
- [ ] Cost preview + confirm: always print token/price estimate before the API call;
      `--yes` to skip the confirmation; keep `--dry-run` as estimate-only
- [ ] `transcribe` command: `--whisper-model` (default from config; notebook uses
      `medium.en`) and `--gpu/--no-gpu` passthrough
- [ ] Idempotent re-runs: `extract-audio` and `transcribe` skip work when outputs already
      exist (`--force` to override) — mirrors the notebook's skip-if-exists guard and gives
      cheap resume (integration test: second invocation is a no-op)
- [ ] Fix the `--model` choice lists in `cli.py` (currently stale, e.g. `claude-3-5-sonnet`;
      derive from `summarize_transcript.anthropic_models` instead of hardcoding)
- [ ] Light interactive mode (`minutia go` or `--interactive` on `process-all`): rich/typer
      prompts — pick MKV from a newest-first list out of `recordings_dir`, choose prompt
      kind, confirm cost, then run the normal pipeline path (a *full* guided TUI is
      deferred — see BACKLOG "Guided TUI mode")
- [ ] **Milestone check**: run one real meeting end-to-end with only CLI commands; retire
      the notebook for daily use

### Phase 5: Eval Seams — NOT STARTED
- [ ] `clients/summary_client.py`: `SummaryClient` protocol —
      `complete(system_prompt, text, *, model, max_tokens, temperature) -> str` — plus
      `AnthropicSummaryClient`; refactor `generate_long_summary`/`generate_summary` to accept
      a client (default Anthropic) instead of constructing one inline (TDD with a fake client)
- [ ] Run-metadata sidecar: every summarize run writes `<report>.run.json` next to its output
      via `run_metadata.py` — transcript path + content hash, prompt kind + prompt hash,
      model, params, token counts, estimated cost, timestamps, output path (unit test:
      sidecar schema round-trips)

### Phase 6: Orchestrator Hardening & Baseline Retirement — NOT STARTED
- [ ] Add `prompt_kind`, `notes_path`, `personal_info_path`, `generate_markdown` fields to
      `PipelineConfig`; wire the summarize step through the same
      prompt-registry + `generate_long_summary` + report path the CLI uses
- [ ] End-to-end test: `PipelineOrchestrator` run against a fixture scenario produces the
      summary, the `.md` report, and the run-metadata sidecar
- [ ] Update `README.md` to document the CLI as the entry point (it still documents
      `baseline_pipeline.py`)
- [ ] Delete `src/minutia/baseline_pipeline.py` + `tests/integration/test_baseline_pipeline.py`
      once the above passes — **do not delete before Phase 6 lands**

## Details

**Target architecture**:
```
src/minutia/
├── cli.py / config.py / logging.py / paths.py / prompts.py / run_metadata.py
├── legacy/          # isolated Jupyter-era code
├── clients/summary_client.py   # SummaryClient protocol + AnthropicSummaryClient
├── pipeline/orchestrator.py
└── steps/{video_extraction,audio_transcription,transcript_merger,summarize_transcript}.py
```

**Why the parity target changed** (2026-07-02 PLAN session): the spec previously measured
parity against `baseline_pipeline.py`/`CreateTranscriptProd.ipynb`, but the workflow evolved —
`SummaryPromptVariations.ipynb` is what actually gets used, and it already runs on
`minutia.steps.*`. Its driver-level behaviors are the requirements: prompt registry keyed by
kind (6 kinds), per-meeting `markdown_notes` (speaker/track mapping + notes) and
`personal_info` injected into the system prompt, cost estimate + transcript preview before
spending API money, AI-named markdown report, skip-if-exists idempotency, whisper
`medium.en` + GPU.

**Per-meeting context = files via flags.** `--notes notes.md` and `--personal-info me.md`,
with `personal_info` (stable across meetings) defaultable from config so it's set once.
Chosen over a discovered `meeting.yaml` (new schema + discovery logic = surface area) and
over interactive prompting (untestable/unscriptable). This **replaces the former Phase 4
"Soul" design** (`SOUL.md`/`HEARTBEAT.md`/`NOTES.json` overrides), which described a
mechanism the real workflow never adopted.

**Paths & config design** (2026-07-02 PLAN(2)). Problems found: the output default was
`./runs` relative to CWD (artifacts scatter by invocation dir); config files loaded from CWD
only (the user-global `~/.minutia` documented in AGENTS.md never existed in code); the input
MKV was always a required argument while the notebook had glob-the-recordings-dir
convenience. Design:
- **Artifact home**: `platformdirs.user_documents_path()/"minutia"` — summaries/reports are
  documents the user reads and shares, so they live somewhere visible, not in a hidden data
  dir. The existing `RunPaths` run-directory layout underneath is unchanged.
- **Input**: explicit path always wins; bare invocation resolves the newest `.mkv` in
  `recordings_dir` (config/env), echoing the pick. Two entry styles: power-user flags, and a
  light interactive `minutia go` (rich prompts). Full guided TUI → BACKLOG.
- **Config precedence**: CLI flag > env var > CWD `.env`/`.minutia` > user-global
  `platformdirs.user_config_path("minutia")/config.env` > platformdirs defaults. A
  `minutia config` command prints each resolved value and its source.
- **platformdirs** is a tiny pure-Python dep and the right call ahead of open-sourcing —
  correct locations on Linux/macOS/Windows for free. Reference notes: `_snap/context/platformdirs/`.

**Typer over Click** (2026-07-02 PLAN(2)): user preference, consistent with the
`snap-script` convention (typer + loguru). Typer is built on Click so the port is
mechanical; do it 1:1 *before* the parity features so new commands are written once, in
typer. Bonus: enum-typed choices replace the hardcoded `--model` string lists, and rich
help output comes free. `pyproject.toml` and AGENTS.md's dependency list update with it.

**Eval seams rationale** (kept deliberately small; harness lives in opensource_portfolio):
- `SummaryClient` protocol: makes provider a parameter of the summarize step, so local-LLM
  (Ollama) support and evals over LLMs × prompts become drop-ins, not refactors.
- Run-metadata sidecar: every real run becomes an eval datapoint; comparing
  prompts/models/transcription settings later is "re-run step over fixtures, diff sidecars."
- Enumerable prompt registry: evals (and `--help`) can iterate `list_prompt_kinds()`.
- Step boundaries stay file-based with stable JSON schemas — the golden-sample scenario
  layout doubles as the eval fixture substrate for transcription comparisons.

**Testing** follows the Golden Sample standard: fixtures in
`tests/fixtures/scenarios/{scenario}/{01_extracted,02_transcribed,03_merged,04_summarized}/`
generated by the trusted legacy notebook; integration tests assert refactored-step output
matches. Generator script: `tests/scripts/generate_golden_samples.py`. Anthropic is always
mocked below the `slow` tier; the `SummaryClient` protocol makes a fake client the natural
mock.

## Known Issues

- FFmpeg output-overwrite handling in `video_extraction.py` was previously reported as failing
  when re-running extraction into an existing output directory (missing an explicit overwrite
  flag). Not confirmed against the current code during this pass — re-verify before closing.

## Source

Consolidated from `_blueprint/features/core-design.md`,
`_blueprint/roadmap/planning/refactor-architecture-spec.md`,
`_blueprint/roadmap/planning/refactor-testing-guide.md`, and
`_blueprint/roadmap/REFACTOR_ACTION_PLAN.md` (originals archived under `_snap/archive/`).
