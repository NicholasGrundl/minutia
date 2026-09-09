# Session — cli-wizard-redesign · Task 1: scaffold the `cli/` package

*The present — an ephemeral working scratchpad. Wiped at flush; nothing durable belongs here.*

## Focus

Feature: [`[active]cli-wizard-redesign`](./features/%5Bactive%5Dcli-wizard-redesign.md).
**Task 1 of 8 — Scaffold the `cli/` package.** Pure restructure, **no behavior change**: split the
flat 672-line `src/minutia/cli.py` into a `cli/` subpackage. All current commands
(`extract-audio` / `transcribe` / `merge-transcripts` / `summarize` / `process-all` / `go` /
`config`) keep working identically. Removal of `go`/`process-all` and the new `run`/`info` groups
are Tasks 3–4, NOT here.

Scaffold scope = **minimal move** (user decision): `app.py` (all current commands) + `_steps.py`
(shared helpers) + `__init__.py`. `run.py` / `setup.py` / `info.py` / `wizard/` get created in their
own later tasks (no empty stubs now).

## Sub-tasks (just-in-time)

- [x] 1. `git mv src/minutia/cli.py → src/minutia/cli/app.py`; created the `cli/` package.
- [x] 2. Extracted shared step helpers into `cli/_steps.py` (`_extract_audio_step`,
      `_transcribe_step`, `_summarize_step`, `_read_optional_text`, `_resolve_notes_answer`,
      `_resolve_input_or_fail`); `app.py` imports from it. Relative imports rebased `.` → `..`.
- [x] 3. `cli/__init__.py` re-exports `main` only (NOT the Typer `app` — see gotcha below);
      `minutia.cli:main` entry point + `CliRunner` imports confirmed working.
- [x] 4. Retargeted tests' monkeypatch paths (`_steps` for step wrappers, `app` module for
      `process_transcripts`/`resolve_settings`/`PipelineOrchestrator`; `llm_mock.py` too). Gate
      green: ruff + ty clean; `pytest -m "unit or integration"` = 100/100 in deterministic order.

### Task 2 — cold-start discipline ✅ (done)

- [x] 1. `cli/_steps.py`: heavy step imports (`video_extraction`/`audio_transcription`/
      `summarize_transcript`) moved **lazy**, inside the functions that run them.
- [x] 2. **ROOT CAUSE was `src/minutia/__init__.py`** — it eagerly imported the whole heavy stack
      (`from .steps import audio_transcription, summarize_transcript, …`), so ANY `minutia.X`
      import (incl. the CLI) pulled torch/whisper/anthropic. Slimmed it: light imports + the four
      heavy step modules exposed **lazily via PEP 562 `__getattr__`**. Back-compat preserved
      (`minutia.audio_transcription`, `from minutia import transcript_merger` still work).
- [x] 3. `app.py`: added eager `--version` callback (prints installed version via
      `importlib.metadata`, → `0.3.0`; exits before settings/logging run).
- [x] 4. Retargeted the lazy-step monkeypatches to the **source module** seam
      (`minutia.steps.audio_transcription.process_audio_files`, `…video_extraction.process_mkv_file`)
      — that's where the lazy import resolves at call time. Added
      `tests/unit/test_cli_cold_start.py` (subprocess probe: `--version`/`--help`/`config` import
      no torch/whisper/anthropic). Gate green: ruff + ty clean; **101/101** deterministic.

**Verified:** `import minutia.cli` + `--version`/`--help`/`config` → torch/whisper/anthropic all
absent from `sys.modules`. Heavy stack loads only when a step actually runs.

## Notes / reasoning / gotchas

- Tests monkeypatch module-level names on `minutia.cli`: `process_mkv_file`, `process_audio_files`,
  `process_transcripts`, `PipelineOrchestrator`, `resolve_settings`, `_resolve_notes_answer`. After
  the split these move — retarget the monkeypatches to wherever each name lives (`app` or `_steps`).
  Spec explicitly allows adjusting tests "only for import paths."
- `main = typer.main.get_command(app)` (the click-command object) must stay reachable as
  `minutia.cli.main` for `CliRunner` and the `minutia.cli:main` console entry point in pyproject.
- **GOTCHA (naming collision):** re-exporting the Typer instance as `app` in `cli/__init__.py`
  *shadows* the `app` submodule — `minutia.cli.app` then resolves to the Typer object, breaking
  module-level patching (`monkeypatch`/`mocker.patch` both walk attributes, not sys.modules). Fix:
  `__init__` re-exports **only `main`**; the Typer lives at `minutia.cli.app.app`. Nothing imported
  the package-level `app`, so no loss.
- **PRE-EXISTING test fragility (not the restructure):** the old `mock_llm` fixture patches
  `resolve_settings` in a way that leaks across module boundaries; under `pytest-randomly` ordering
  it can fail `test_cli_process_all`. Passes in isolation + deterministic order (100/100). → folds
  into the user's planned DI-mocks rework.

## User steers this session (shape later tasks)

- **Tests:** don't over-index on the current CLI tests — fine to turn off / retire the ones tied to
  the old surface (`go`, `process-all`) and write sensible new ones once the CLI is functioning
  (aligns with Tasks 3 & 8 already removing that surface).
- **DI mocks:** user plans to reimplement mocked aspects as **dependency-injected** doubles, easier
  to test. Shape `cli/_steps.py` + the wizard cores toward injection (constructor/param seams) as
  the `run` group (Task 3) and wizard (Task 6) build on them.
- **USER NOTE (surface at Task 5, `wizard/tui.py`):** user wants to customize colors / style /
  banner details — **pause and get their input** at that stage before finalizing the chrome.

## Nits noticed (not fixed — out of scope, revisit)

- `src/minutia/__init__.py` still has `__version__ = "0.1.0"` (stale; pyproject is `0.3.0`). The
  CLI `--version` reads installed metadata (correct `0.3.0`), so this only affects `minutia.__version__`.
  Left untouched to keep the cold-start task focused; worth aligning in a cleanup/ALIGN pass.

## Open / blockers

- none. Tasks 1 + 2 done (scaffold + cold-start). Next: Task 3 (the `run` command group — run-all +
  the four step subcommands on the shared `_steps` helpers; **removes `go`/`process-all`** from the
  surface) OR checkpoint/commit Tasks 1–2 first (user's call). Reminder: Task 5 (`wizard/tui.py`) is
  the colors/style/banner checkpoint the user asked to weigh in on.
