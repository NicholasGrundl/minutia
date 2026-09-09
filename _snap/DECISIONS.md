# Decisions

Append-only, culled log of what was done and why — the **past**. Read this to onboard. Each
entry: *what we set out to do / why / how it ended / why we stopped*. Newest first.

Session scratch lives in [`SESSION.md`](./SESSION.md); it is condensed into here at session
close.

---

## 2026-09-09 — promotion + first releases shipped; reprioritization after stabilization

- **Set out to:** (BUILD/discussion session) Take stock now that the base is stable, reconcile the
  spine with what actually shipped, and re-order the ROADMAP around current priorities. The prior
  flush left `ci-release-pipelines` `[active]` with the real release "deferred until workflows land
  on main" — but a lot landed since, outside snap sessions.
- **Why:** The ROADMAP was stabilization-era and no longer reflected reality: the base is on `main`,
  CI + releases are live, and two versions are out. User called it: "the ROADMAP is good but may not
  reflect the priorities now that things are stabilized."
- **What actually shipped (the unflushed drift, now reconciled):**
  - **PR #1** — `uv_refactor → main` promotion: the entire stabilized base (uv + just + ty,
    settings-resolution, CLI parity, tiered tests) landed on `main`. `uv_refactor` retired.
  - **PR #2** — `ci-release-pipelines` merged; `ci.yml` (lint + `ty`, no pytest) and `release.yml`
    (tag-driven GitHub Releases) are now live on `main`.
  - **PR #3** — CPU-only torch in CI (GPU stays the local default) — CI hardening follow-up.
  - **Releases:** `v0.2.0` (validated `release.yml` end-to-end — task 7) and `v0.3.0` (carries the
    PR #3 fix). `pyproject` is `0.3.0`; both tags published.
  - **Spine effect:** `ci-release-pipelines` → `[done]` (frontmatter + checklist updated; awaiting
    the `[active]→[done]` git mv). ROADMAP Section A + item 4 are complete.
- **Reprioritization decision (user):** **finish the refactor tail first** —
  `eval-seams` (keystone: unblocks evals + local-LLM, adds the `run.json` sidecar) → then
  `orchestrator-retire-baseline` (its e2e test depends on eval-seams). **Dogfood in parallel** on
  real meetings; findings logged to `_snap/reference/dogfood-findings.md` to feed the expansion
  decision. The parked §C vision drafts (OBS recorder, background-process, sql-job-tracking,
  video-filestore, local-llm, evals-harness) become a *decision checkpoint after the tail*, steered
  by dogfooding — not a committed order yet.
- **How it ended:** ROADMAP rewritten (Done / Now / In parallel / Next-checkpoint / Later);
  `ci-release-pipelines` closed out; dogfood log seeded. No code changed this session.
- **Why we stopped:** Discussion + ROADMAP update was the whole scope.
- **Next:**
  1. User runs the `git mv "[active]ci-release-pipelines.md" "[done]ci-release-pipelines.md"` (its
     own commit, per convention).
  2. Next BUILD session: flip `eval-seams` `[ready]→[active]` and start task 1 (`SummaryClient`).
  3. Housekeeping (deferred, non-blocking): `BACKLOG.md` still holds stale items from an unrelated
     project (LanceDB/metrochat/SDS retrieval, D3 web-app `context/` folders) — flag for a future
     ALIGN/prune.

## 2026-09-09 — ci-release-pipelines: CI + release tooling authored and validated (feature [active])

- **Set out to:** Author the CI/release half of the tooling modernization — tasks 2–6 of the
  spec: `scripts/release.py`, `.github/workflows/ci.yml` + `release.yml`, justfile `tag-*`
  recipes — adapted from the sibling-project templates at `_snap/reference/ci_content/`.
- **Why:** With `main` promoted (PR #1) and the base green, the branch precondition was met; a
  lint/type gate on `main` plus reproducible tagged releases is the next block off the new trunk.
- **How it ended:** Done for tasks 2–6, all validated locally.
  - `scripts/release.py` ported near-verbatim (dirty-tree + existing-tag guards, the
    `uv version --bump --dry-run --short` preview, `chore: release <tag>` commit). Dry-run
    previews `v0.1.1`; both guard warnings fired (dirty tree; a throwaway `v0.1.1` tag, since
    deleted). ruff clean (scripts/ is outside the gate — verified anyway).
  - `ci.yml`: on push-`main` + PRs — checkout, `setup-uv@v6` (uv pinned `0.12.12` + cache),
    `uv sync`, `ruff format --check` + `ruff check` over `src tests` (matches the local gate, not
    the reference's `.`), `ty check` (no path arg — scope lives in `[tool.ty.src]`). No pytest,
    per spec.
  - `release.yml`: on push tags `v*`, `contents: write`, guard `tag == v$(uv version --short)`,
    `softprops/action-gh-release@v2` with `generate_release_notes`. Both YAMLs parse.
  - `justfile`: new Release section, `tag-patch|minor|major` → `scripts/release.py`.
- **Why we stopped:** Tasks 2–6 complete; task 7 (cut the first real release, likely `v0.2.0`) is
  deferred by design — the workflows only fire once they are on `main`, so the real release waits
  until this branch merges. Feature stays `[active]`.
- **Next:**
  1. Commit: the flip (rename + frontmatter + ROADMAP `[active]`) as its own commit; the four
     authored files (+ this flush) as the `[MACRO] ci-release-pipelines` checkpoint.
  2. PR `ci-release-pipelines → main`; on merge `ci.yml` goes live on `main` + PRs.
  3. Post-merge: cut the first release via `just tag-minor` (0.1.0 → `v0.2.0`) to validate
     `release.yml` end-to-end, then flip the feature `[active]→[done]`.

## 2026-09-09 — tool-install: uv tool install interpreter fix + setup docs (committed e72a8b5)

- **Set out to:** Fix installing minutia as a `uv` tool — it required a forced `--python 3.12` —
  and document the smoothed flow, since the user's preferred run mode is `uv tool install`.
- **Why:** `uv tool install` kept selecting Python 3.14 (no torch `cp314` wheels) and failing to
  resolve, forcing the manual pin.
- **How it ended:** Done. Root cause: uv `0.9.10` ignored the `requires-python <3.14` cap during
  interpreter selection for git/local tool installs (and `.python-version` is ignored by tool
  installs entirely). `uv self update` → `0.12.12` fixed it — install now auto-picks 3.12.12 with
  no flag. Standardized on installing from git `main` over HTTPS via the `gh` credential helper
  (`gh auth setup-git`). Wrote `docs/setup.md` (tool-install primary + SSH alternative +
  interpreter note + old-uv fallback ladder + dev-from-clone); README §Install dropped the
  `--python` workaround and links it. The `requires-python` cap and torch pin were left as-is
  (already correct). Committed as MACRO `e72a8b5`.
- **Why we stopped:** Install works cleanly; docs written and committed.
- **Next:** CI pins uv (`0.12.12`) via `setup-uv` so it can't regress to the ignoring behavior
  (folded into the ci-release-pipelines work above).

## 2026-09-09 — finish-cli-parity: real-meeting run validated; refactor_to_cli closed

- **Set out to:** Prove the CLI at parity with the notebook by running one real meeting
  end-to-end, CLI-only — the live milestone that lets `refactor_to_cli` close.
- **Why:** Everything short of a live Whisper + Anthropic run was already validated against the
  golden-sample fixtures; this was the human-in-the-loop confirmation on real audio, and the last
  gate before the `uv_refactor → main` PR.
- **How it ended:** Done. `minutia go` ran a real ~2.4h recording fully: 3 audio tracks extracted,
  GPU Whisper `medium.en` on both tracks (mic 739 + desktop 299 → 1323 merged segments), then the
  AI-named markdown report. Transcript quality, merge ordering, and summary shape matched notebook
  expectations.
  - **Dogfood finding (fixed):** the guided `go` notes prompt silently required a *file path* —
    typing prose ('microphone track is Nick Grundl, desktop track is client') raised
    `Notes file not found`. Fixed to accept inline text OR a path: new `_resolve_notes_answer` in
    `cli.py` (existing file → used as path; otherwise persisted to `<output_dir>/notes.md` and fed
    to the summarizer), prompt relabeled 'Notes (text or a file path; blank for none)', plus a
    `TestResolveNotesAnswer` unit test. Gate green: ruff + ty + **100 pytest**.
  - **Notebook retired** as the daily driver — CLI is now the primary path. The notebook files
    remain a documented fallback until `notebooks-clean-rebuild` (README still links them).
  - **Spine:** `finish-cli-parity → [done]`, `refactor_to_cli → [done]` (plain `mv` renames);
    ROADMAP section A is now fully `[done]` and the promotion PR is marked unblocked; sibling-spec
    `Source:` pointers repointed to `[done]refactor_to_cli.md`.
- **Why we stopped:** Milestone complete; `refactor_to_cli` closed.
- **Next:**
  1. The go notes-prompt bugfix is uncommitted in the working tree (plus these spine edits) —
     land as a `[MACRO] fix(finish-cli-parity)` checkpoint.
  2. **Promotion:** PR `uv_refactor → main`, then retire `uv_refactor`. Base is stable + green.
  3. Post-merge / feature branches off the new `main`: `ci-release-pipelines`, then the two
     remaining `refactor_to_cli` tail specs (`eval-seams`, `orchestrator-retire-baseline`).

## 2026-09-08 — tests-refactor: tier triage + tests into the lint/type gate (checklist complete)

- **Set out to:** Finish the two open `tests-refactor` tasks — the pre-stabilization test work
  gating the `uv_refactor → main` PR: (1) triage/group every test into `unit`/`integration`/`slow`
  and add a `tests/slow/` real-key guard; (2) bring `tests/` into the ruff + ty gate.
- **Why:** The ROADMAP promotion milestone requires a green, tiered suite in the gate before the PR;
  4/6 of the checklist was already done in the settings-resolution session, leaving these two.
- **How it ended:** Done — full gate green: `ruff check/format src tests` clean, `ty check` passes,
  **97 passed** (83 unit / 14 integration / 0 slow / **0 unmarked**).
  - **Tiering by directory (single source of truth):** added `pytest_collection_modifyitems` to
    `tests/conftest.py` that marks each test `unit`/`integration`/`slow` from its top-level dir.
    Removed the now-redundant per-file `pytestmark`/`@pytest.mark.<tier>` (and the freed
    `import pytest` in `test_generate_golden_samples.py`). Chosen over explicit per-file markers to
    permanently kill the marker-drift class (user decision). `git mv tests/test_mocks_sanity.py →
    tests/unit/` so it falls under the unit dir.
  - **`tests/slow/` scaffold:** new dir (`__init__.py` + `conftest.py`). The root autouse env-scrub
    deletes `ANTHROPIC_API_KEY`, so the slow guard captures the real key at *import* time and, for
    slow tests only, re-injects it past the scrub; skips the whole tier when no real `sk-ant-…` key
    is present. No real-calling slow test added yet (future eval-seams/real-model work lands here).
  - **Gate expansion:** `justfile` `lint`/`format`/`ruff` recipes `src → src tests`;
    `[tool.ty.src].include = ["src", "tests"]`, excluding `tests/scripts/` (fixture-gen tooling +
    a notebook with optional-only deps GPUtil/psutil and stale APIs — not the suite proper).
  - **ty-in-tests reality check:** the prior session's "ty check src tests passes" was inaccurate —
    with tests actually in the gate, ty found 13 diagnostics in real test files (all type-inference
    gaps over dynamic patterns — dict `**kwargs` into `PipelineConfig`, a `get_prompt_builder()`
    callable ty can't see the signature of, an `object`-typed capture dict — **not** runtime bugs;
    suite green). Per user decision, **baselined all 13** via a dedicated `[[tool.ty.overrides]]`
    block (mirrors the existing 9-error src baseline), scoped per-file + per-rule so new errors
    still fail. Tightening those seams (annotate the test local; give `get_prompt_builder` a
    `Callable`/`Protocol` return) is tracked follow-up debt.
- **Why we stopped:** All six `tests-refactor` checklist items are now complete; natural close.
- **Next:**
  1. `[draft]tests-refactor.md` is checklist-complete → flip `[draft]→[done]` (a separately-approved
     `git mv` + frontmatter `state`, per `_snap` convention). Content is already updated/ticked.
  2. Macro-commit this checkpoint (message drafted in session).
  3. The pre-PR "once-through of the tests" item on the promotion milestone is satisfied; the
     remaining pre-PR item is the `README.md` update (make→just, install/usage, anthropic 1.x).
  4. Follow-up debt (not blocking): drive both ty baselines (9 src + 13 tests) to zero; fix the
     latent None-subscript bug in `steps/summarize_transcript.py`.

## 2026-09-08 — settings resolution + test-suite stabilization (code complete, gate handoff)

- **Set out to:** Fix the production configuration design exposed by the test-suite environment
  leak, test the new stable boundary, then return to the deferred suite failures without inventing
  production APIs for stale tests.
- **Why:** The hand-written loader called `load_dotenv()` and mutated `os.environ`, so config loads
  were stateful and provenance could be false. At the same time, pytest inherited legitimate
  developer settings and could select a real recording, causing an ffmpeg hang.
- **How it ended:** The settings feature is code-complete and the previously failing suite reached
  **97 passed / 0 failed / 0 skipped** before the final mechanical test formatting pass.
  - **Settings boundary:** added `pydantic-settings`; removed direct `python-dotenv`. The public
    boundary is now `MinutiaSettings` plus immutable `SettingsResolution`, produced by
    `resolve_settings()`. Per user direction (pre-v0, no users), the old `MinutiaConfig`,
    `load_config()`, `env_sources`, and environment-reading API-key compatibility helper were
    removed rather than shimmed.
  - **Resolution policy:** defaults < platformdirs `config.env` < one cwd-contextual `.env` <
    process environment < CLI arguments. `discover_env_file()` selects the nearest file, stops at
    `.git`/`pyproject.toml` or before home, and never anchors to input/output. File-declared paths
    are relative to their file; environment/CLI paths are relative to the invocation directory.
    `--env-file` and `--no-env-file` are global CLI options; `minutia config` reports discovery and
    winning sources without exposing the key.
  - **Explicit dependencies:** summarize/report helpers now require an explicit `api_key`; CLI,
    orchestrator, baseline fallback, mocks, and fixture scripts receive resolved settings instead
    of independently rereading process state.
  - **Settings tests:** expanded focused config/CLI coverage to 29 passing tests (precedence,
    aliases, validation, boundaries, explicit/disabled discovery, path anchoring, provenance, and
    no process mutation). The full unit directory passed **79/79** at that checkpoint.
  - **Suite isolation:** root autouse fixture scrubs `MINUTIA_*`, `ANTHROPIC_API_KEY`, and
    `CLAUDE_API_KEY`; the skipped CLI test was re-enabled. `pytest-timeout` is now a dev dependency
    with `--timeout=60` in pytest defaults.
  - **Stale e2e tests:** rewrote `test_e2e_permutations.py` against the orchestrator's real default
    step adapters and correct chaos triggers. No aliases/adapters were added to production. The
    five failures now pass, including partial completion and artifact preservation.
  - **Test hygiene:** mock fixtures are registered via top-level `pytest_plugins`; Anthropic mocks
    match the explicit-key/current-client boundary. Ruff safe-fixes + formatting were applied to
    `tests/`; `ruff check tests` and `ty check src tests` both pass.
  - **Docs:** updated AGENTS, README, the running guide, source atlas, active CLI-refactor spec,
    settings spec, and tests-refactor spec for the new configuration tree.
- **Why we stopped:** User requested a session flush so a fresh BUILD session can perform the final
  gate work with compact context.
- **Next:**
  1. Persist the already-validated gate expansion: `[tool.ty.src].include = ["src", "tests"]` in
     `pyproject.toml`; change `justfile` lint/format/ruff recipes from `src` to `src tests`. A combined
     patch was attempted but did not apply, so neither of those scope edits was made.
  2. Run `just lint`, `just ty`, and plain `uv run pytest` (the timeout is now built in). The last
     full green run preceded the final mechanical Ruff formatting, so repeat it once.
  3. Finish the remaining tests-refactor tier work: ensure every test is deliberately marked
     unit/integration/slow and decide whether tier-specific conftests need any additional autouse
     bundles. Then update the feature checklists.
  4. `settings-resolution` is checklist-complete but remains `[active]`; any filename state change
     requires the repository's separately approved `git mv` workflow.

## 2026-09-08 — stabilization / editable-install + anthropic 1.x fixes (post-migration dogfooding)

- **Set out to:** Clear loose ends so `uv_refactor` can PR → `main` in a workable state — install
  minutia as an editable `uv` tool and run it on a real recording.
- **Why:** Dogfooding the CLI end-to-end before promotion surfaced two install/runtime blockers.
- **How it ended:** Done — CLI installs editable and runs `go`/`summarize` end-to-end on a real
  meeting. Committed as `[MACRO] fix(stabilization)`.
  - **install:** `uv tool install` defaults to the newest interpreter (3.14) and **ignores the
    project `.python-version`**; torch has no cp314 wheels → resolution failed. Capped
    `requires-python <3.14` (torch stays 2.5.1). Workaround if needed: `--python 3.12`.
  - **anthropic 0.x→1.x:** unpinned `anthropic` drifted to 1.x in the tool env (dev was 0.102).
    1.x **removed sampling params from `messages.create()`** → `TypeError` on `temperature`.
    Removed `temperature` from the 3 `create()` calls; pinned `anthropic>=1.4`; re-locked; dev
    now 1.4.0 == tool. Verified: `summarize` wrote an AI-named report on a real transcript.
  - **docs:** added `docs/running-the-pipeline.md` (tiered run guide).
  - **tests:** parked deferred debt as `[draft]tests-refactor.md` + ROADMAP entry.
- **Findings:**
  - `ty` earned its keep — the baselined `no-matching-overload` on `messages.create` *was* this
    bug. Un-baseline it during tests-refactor.
  - The None-subscript `ty` flagged in `summarize_transcript` is guarded by a `KeyError` above —
    not a real bug.
  - **Full test suite hangs under anthropic 1.x** (`llm_mock` is 0.x-shaped → a real API call).
    Don't debug via full-suite runs; tracked in tests-refactor.
- **Why we stopped:** increment committed + validated on a real meeting.
- **Next (to finish the PR → stable `main`):** (1) **update README** (make→just, install/usage,
  anthropic 1.x + python `<3.14` notes); (2) **do a once-through of the tests together** (triage/
  group + rework fixtures/mocks per `[draft]tests-refactor.md`). Then PR `uv_refactor` → `main`.

## 2026-09-08 — justfile-migration / justfile + `ty` adopted (code complete)

- **Set out to:** Replace the `Makefile` with a `justfile` task runner and adopt Astral's `ty`
  as the type checker, on the base (`uv_refactor`) so it rides along at `main` promotion.
- **Why:** Dev-facing half of the tooling modernization (`EXECUTIVE_SUMMARY.md`); matches the
  sibling project's `just`+`ty` loop. CI/release half is the separate `ci-release-pipelines`.
- **How it ended:** Code done.
  - **`justfile`** authored (repo root): `sync`/`sync-all`, `lint`, `format`, `ruff` (mutating),
    `ty`, `check-all` (= ruff + ty + test), `test *args` + tiers, `create-env-file`, `jupyter`,
    `clean`. Dropped `commit`/`test-codex`/`lint-codex`/`install-jupyter`.
  - **`ty==0.0.79`** added to the `dev` group; `[tool.ty]` config pins `python-version=3.12`.
  - **Gate scoped to `src`** (not `src`+`tests`) — user decision: `tests/` has ~28 lint + 13
    format items of pre-existing debt and will churn in the coming test refactor, so cleaning +
    gating tests is deferred to a future **tests-refactor** feature. `tests/` left untouched.
  - **`ty` triage:** 48 → 26 (scoping) → 9 real src errors. Large count → **baselined** via a
    narrow per-file `[[tool.ty.overrides]]` (4 rules, 4 files); `just ty` exits 0. Found a latent
    bug (None-subscript on unknown model in `summarize_transcript.py`) — logged, not fixed.
  - **`just check-all`:** ruff + ty GREEN on `src`; `test` step surfaces the 5 pre-existing e2e
    failures (`test_e2e_permutations.py`) — deferred, unchanged from baseline (74 passed / 5 fail).
  - **Gotcha:** `ruff check --fix` deletes conftest fixture re-imports (F401) — a reason tests
    stay out of the mutating recipe until fixtures are registered idiomatically.
- **Why we stopped:** Code complete. Two `_snap`-etiquette git ops handed to the user:
  `git mv` the spec `[ready]→[active]` (then `→[done]`) and `git rm Makefile` (each its own commit).
- **Next:** User runs the two git ops + a `[MACRO]` commit; then `justfile-migration` → `[done]`.
  Follow-ups tracked under ROADMAP "Known issues" (ty baseline debt; tests-refactor feature).

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
