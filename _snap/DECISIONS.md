# Decisions

Append-only, culled log of what was done and why — the **past**. Read this to onboard. Each
entry: *what we set out to do / why / how it ended / why we stopped*. Newest first.

Session scratch lives in [`SESSION.md`](./SESSION.md); it is condensed into here at session
close.

---

## 2026-07-02 — refactor_to_cli / Phase 4 code COMPLETE: notebook-parity CLI + minutia go

- **Set out to:** All Phase 4 tasks in one session: summarize upgrade, cost confirm,
  transcribe options, idempotent re-runs, model-list fix, `minutia go`.
- **Why:** This is the daily-use milestone — the CLI replaces SummaryPromptVariations.ipynb.
- **How it ended:** Code done; live milestone (a real meeting, CLI-only) awaits the user.
  - **model_registry.py** (new): `anthropic_models` moved out of the summarize step into a
    cycle-free module; `SUMMARY_MODEL_CHOICES = tuple(anthropic_models)`; config default →
    `claude-sonnet-4-6` (was `claude-4-5-sonnet`, which wasn't even a registry key — the
    default `minutia summarize` path had been raising KeyError, and the long-failing
    `test_baseline_pipeline_smoke` turned out to be this too; it now passes → known
    pre-existing failures dropped from 6 to the 5 in test_e2e_permutations.py).
  - **summarize** now: `MERGED [OUTPUT_DIR]` (default: next to the transcript), --prompt-kind
    /--notes/--personal-info (personal-info defaults from config), timestamped transcript
    prep via `extract_transcript_text` (moved into the step; baseline re-exports; notebook
    imports), estimate + typer.confirm gate (--yes), --dry-run, `generate_long_summary`
    → AI-named markdown report. BREAKING: output arg changed from file to directory.
  - **transcribe**: --whisper-model/--gpu passthrough. **Idempotency**: extract-audio +
    transcribe skip when outputs exist (--force), matching the notebook guard.
  - **minutia go [PATH]**: guided flow (numbered newest-first MKV pick, prompt-kind pick,
    optional notes, cost confirm) chaining the same skip-aware helpers; artifacts under
    `base_output_dir/<recording-stem>/`. Optional directory argument (`minutia go .`)
    browses that path instead of the configured recordings dir (user request, same day).
  - Shared `_extract_audio_step`/`_transcribe_step`/`_summarize_step` helpers back both the
    step commands and `go`. `mock_llm` fixture gained recordings_dir/personal_info_path.
  - 8 new unit tests (`test_cli_phase4.py`); suite 73 passed / 5 known failures; help smoke
    on all 7 commands; AGENTS.md CLI docs rewritten.
- **Next:** user runs the milestone check on a real meeting; then Phase 5 (eval seams:
  SummaryClient protocol + run-metadata sidecar), then Phase 6 (orchestrator + baseline
  deletion).

## 2026-07-02 — refactor_to_cli / Phase 3 COMPLETE: platformdirs config/paths + minutia config

- **Set out to:** The four remaining Phase 3 tasks (coupled, one session): platformdirs
  defaults in `config.py`, user-global config file, input-resolution helper,
  `minutia config` provenance command.
- **Why:** Kill the CWD-dependent `./runs` default, give set-once config a real home ahead
  of open-sourcing, and make bare `minutia process-all` grab the newest recording.
- **How it ended:** Done —
  - `config.py` rewritten around layered resolution with per-key source tracking
    (`MinutiaConfig.sources`): environment > CWD `.env`/`.minutia` > user config
    (`~/.config/minutia/config.env` via platformdirs) > defaults. New fields
    `recordings_dir` (MINUTIA_RECORDINGS_DIR) and `personal_info_path` (MINUTIA_PERSONAL_INFO).
    `base_output_dir` default is now `platformdirs.user_documents_path()/minutia`.
    `load_dotenv` mutation kept (now incl. user config) so downstream
    `resolve_anthropic_api_key()` callers keep working.
  - `paths.resolve_input_video(explicit, recordings_dir)`: explicit wins; else newest
    `.mkv` by mtime; actionable ConfigurationError otherwise (lazy config import to avoid
    the config→paths cycle). `input_video` is now optional on `extract-audio` and
    `process-all`; discovery echoes the picked file.
  - `minutia config` prints every value with its source layer, the user-config path, and
    the precedence line; API key masked. Verified live.
  - AGENTS.md env-var + precedence sections updated (no longer 'Future').
  - 11 new unit tests (`test_config_resolution.py`, `test_cli_config_command.py`);
    suite 64 passed / 6 known pre-existing failures; lint + format clean.
  **Phase 3 is fully ticked.**
- **Next:** Phase 4 — CLI parity with SummaryPromptVariations.ipynb (summarize upgrade with
  --prompt-kind/--notes/--personal-info + markdown report, cost confirm, transcribe
  options, idempotent re-runs, model-list fix, `minutia go`).

## 2026-07-02 — refactor_to_cli / Phase 3: CLI ported from Click to typer (1:1)

- **Set out to:** Port the five CLI commands to typer with no behavior change; swap
  `click` → `typer` in `pyproject.toml`; keep existing CLI tests passing untouched.
- **Why:** First Phase 3 (CLI Foundations) task — user preference, consistent with the
  snap-script convention; Phase 4 parity features get written once, in typer.
- **How it ended:** Done — `cli.py` rebuilt on `typer.Typer` with an `@app.callback()` for
  config loading and Annotated typed params. Key bridge:
  `main = typer.main.get_command(app)` exposes a click-compatible command object, so the
  console-script entry point (`minutia.cli:main`), the package re-export, and
  `click.testing.CliRunner` in `test_cli_process_all.py` all work UNCHANGED. `--model`
  choices are now an Enum derived from `SUMMARY_MODEL_CHOICES` (kills the drift between the
  CLI's hardcoded list and config validation; the stale model *names* themselves are a
  Phase 4 fix). `click.ClickException` retained on error paths for identical exit-code/
  message behavior. AGENTS.md dependency list + architecture note updated.
- **Gotcha logged:** `uv remove click` re-synced the venv and silently dropped the opt-in
  dependency groups (jupyter, diagnostics); restored with
  `uv sync --group jupyter --group diagnostics`. `media`/`experiments` groups were NOT
  restored — re-sync if needed.
- **Next:** Phase 3 continues — platformdirs config/paths defaults (recordings dir,
  output home ~/Documents/minutia, user-global config, latest-mkv discovery,
  `minutia config` command).

## 2026-07-02 — refactor_to_cli / Phase 2 COMPLETE: merger verified vs golden fixtures

- **Set out to:** Verify `transcript_merger.py` against the `03_merged/` golden fixtures —
  the last Phase 2 (logic unification) task.
- **Why:** The goldens were generated by the trusted notebook pipeline; matching them is the
  Golden Sample proof that the refactored merger is faithful.
- **How it ended:** Done — a probe run showed all 4 scenarios (`microphone_only`,
  `noisy_microphone`, `podcast_desktop`, `youtube_desktop`) reproduce their golden
  `transcript` arrays *exactly* (segment-for-segment, including whisper token metadata) with
  `parse_overlaps=False`, and stable metadata (schema_version, parse_overlaps,
  segment_count, total_duration) agrees. Frozen as the parametrized
  `test_merger_reproduces_golden_fixture` (marked `integration`) in
  `tests/integration/test_transcript_merger.py`. Golden metadata's run-specific parts
  (source paths, timestamps, per-source blocks) are deliberately excluded from comparison.
  Suite: 53 passed / 6 known pre-existing failures. **Phase 2 is fully ticked.**
- **Next:** Phase 3 — CLI Foundations: port the 5 Click commands to typer 1:1, then
  platformdirs config/paths defaults (output home, recordings dir, user-global config,
  latest-mkv discovery, `minutia config` command).

## 2026-07-02 — refactor_to_cli / Phase 2: report helpers moved into steps/

- **Set out to:** Move `get_filename_from_content` + `create_markdown_report` from
  `baseline_pipeline.py` into `steps/summarize_transcript.py`.
- **Why:** Third Phase 2 task; the summarize step is the module boundary for Anthropic
  integration, and the CLI's Phase 4 `summarize` upgrade will call these from there.
- **How it ended:** Done — functions live in the step (filename prompt imported from
  `minutia.prompts`); `baseline_pipeline.py` re-exports them (still the documented entry
  point, deletable Phase 6); the notebook now imports them from the step too (its local
  copies removed ahead of the spec's schedule — same real-use-parity rationale as the
  registry re-point). Two deliberate adaptations to 'move, not rewrite': default model fixed
  from the stale `claude-3-5-sonnet` (not in `anthropic_models` — default call would
  KeyError) to `claude-sonnet-4-6`, and api-key resolution now follows the steps-file
  convention (`resolve_anthropic_api_key()` + RuntimeError). 4 new unit tests
  (`tests/unit/steps/test_summarize_transcript.py`, mocked via existing `mock_llm`);
  suite at 49 passed / 6 known pre-existing failures; lint + format clean.
- **Next:** Last Phase 2 task — verify `transcript_merger.py` against `03_merged/` golden
  fixtures. Then Phase 3 (typer + platformdirs foundations).

## 2026-07-02 — refactor_to_cli / Phase 2: notebook re-pointed at `minutia.prompts`

- **Set out to:** Make `SummaryPromptVariations.ipynb` (the daily driver) consume the package
  prompt registry instead of its inline builder cells.
- **Why:** Proves registry parity in real use before the CLI takes over; single source of
  truth for prompt flavors.
- **How it ended:** Done — 6 builder-def cells deleted (27→21 cells);
  `generate_meeting_summary_prompt` + `get_filename_prompt` now imported from
  `minutia.prompts` (plus a `list_prompt_kinds()` echo). `extract_transcript_text`,
  `get_filename_from_content`, `create_markdown_report` deliberately remain notebook-local —
  their move into `steps/` is the next checklist task. nbformat validates; headless smoke
  test of the import + prompt-render path passes. NOTE: the notebook itself wasn't executed
  end-to-end (needs whisper/API) — first real run is the true verification.
- **Also:** BACKLOG entry added: "Dev-env modernization: Makefile → justfile, direnv" (user
  is migrating tooling; noted as backlog rather than draft spec, per user).
- **Next:** Phase 2 — move `get_filename_from_content`/`create_markdown_report` from
  `baseline_pipeline.py` into `steps/summarize_transcript.py`; verify merger step against
  `03_merged/` golden fixtures.

## 2026-07-02 — refactor_to_cli / Phase 2: prompt-registry consolidation

- **Set out to:** Make `src/minutia/prompts.py` the single prompt registry: port the three
  builders that existed only in `SummaryPromptVariations.ipynb` (`slide-review`,
  `interview-debrief`, `discovery-summary`), add `get_prompt_builder(kind)` /
  `list_prompt_kinds()`, TDD unit tests.
- **Why:** First task of the re-planned refactor (see the 2026-07-02 PLAN changelog entries in
  the spec): the CLI's `--prompt-kind` will derive its choices from the registry, and prompt
  variants must be enumerable for the future evals harness.
- **How it ended:** Done — all 6 kinds registered; the 3 builders shared with the notebook were
  verified semantically identical (style-only diffs), so no content reconciliation was needed.
  Unknown kinds now raise `ValueError` naming valid kinds (replaces the old silent
  fallback-to-baseline; the notebook's own dispatcher had a latent `.get(kind, 'default')`
  crash bug — not copied). 18 unit tests GREEN in `tests/unit/test_prompts.py`
  (`pytestmark = pytest.mark.unit`); lint + format clean.
- **Gotchas logged:** (1) `pytest -m unit` collected *zero* tests before this session — nothing
  in `tests/unit/` carries the `unit` marker, so `make test-unit` was a no-op; new test module
  is marked, existing ones still aren't. (2) 6 pre-existing integration failures
  (`test_e2e_permutations.py` ×5, `test_baseline_pipeline_smoke`) from stale mock targets /
  `PipelineConfig` signature drift — present before and after this change.
- **Next:** Phase 2 continues — point `SummaryPromptVariations.ipynb` at `minutia.prompts`
  (delete its inline builder cells), then move
  `get_filename_from_content`/`create_markdown_report` into `steps/`.

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
