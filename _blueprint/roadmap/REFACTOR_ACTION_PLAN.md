# Minutia Refactor: Detailed Action Plan

**Reference Documents:**
*   [Architecture Specification](planning/refactor-architecture-spec.md) - Class definitions & file structure.
*   [Testing Guide](planning/refactor-testing-guide.md) - TDD workflow & Golden Sample usage.

---

## Phase 0: Foundation (The Source of Truth)
**Objective**: Establish a trusted baseline for validation. No code refactoring happens here.

### 0.1 Extract Generator Script
- [ ] Create `tests/scripts/generate_golden_samples.py`.
- [ ] Logic Source: `tests/scripts/CreateNewFixtureSet.ipynb`.
- [ ] **Task**: Port the notebook code to a CLI script that iterates over `tests/fixtures/scenarios/` folders.

### 0.2 Generate Golden Samples
- [ ] Run `python tests/scripts/generate_golden_samples.py`.
- [ ] **Verify Artifacts**: Ensure `01_extracted`, `02_transcribed`, `03_merged`, `04_summarized` are populated for:
    - `microphone_only`
    - `noisy_microphone`
    - `podcast_desktop`

---

## Phase 1: Plumbing & Cleanup
**Objective**: Stabilize the package structure so tools work correctly.

### 1.1 Fix Package Entry Point
- [ ] **Edit**: `src/minutia/__init__.py`.
    - **Action**: Remove `cli` import. Add `from .cli import cli`.
- [ ] **Edit**: `pyproject.toml`.
    - **Action**: Change `[project.scripts]` to `minutia = "minutia.cli:cli"`.
- [ ] **Verify**: Run `uv run minutia --help`. It should print the Click help text.

### 1.2 Isolate Legacy Code
- [ ] **Create**: `src/minutia/legacy/`.
- [ ] **Move**:
    - `src/minutia/ui_jupyter.py` -> `src/minutia/legacy/`
    - `src/minutia/claude_audio_widget.py` -> `src/minutia/legacy/`
    - `src/minutia/gpt_audio_widget.py` -> `src/minutia/legacy/`
- [ ] **Update Imports**: If anything in `legacy/` imports from `..`, fix the relative imports.

### 1.3 Reorganize Tests
- [ ] **Move**: `tests/test_paths.py` -> `tests/unit/test_paths.py`.
- [ ] **Move**: `tests/test_pipeline_orchestrator.py` -> `tests/unit/test_orchestrator.py`.
- [ ] **Move**: `tests/test_transcript_merger.py` -> `tests/integration/test_merger.py` (since it reads files).
- [ ] **Verify**: Run `pytest` to ensure discovery still works.

---

## Phase 2: Logic Unification (The "Baseline" Merger)
**Objective**: Move all logic from `baseline_pipeline.py` into `src/minutia/steps/`.

### 2.1 Upgrade Summarization Step
- [ ] **Edit**: `src/minutia/steps/summarize_transcript.py`.
- [ ] **Port Logic**: Copy `generate_long_summary` (continuation loop) from `baseline_pipeline.py`.
- [ ] **Port Logic**: Copy `get_filename_from_content` (AI filename) from `baseline_pipeline.py`.
- [ ] **Implement**: `create_markdown_report(content, output_dir, model_name)`.
- [ ] **Validation**: Create `tests/integration/test_summarization_logic.py` asserting `generate_long_summary` handles mock `[CONTINUE]` tokens.

### 2.2 Verify Merger Step
- [ ] **Edit**: `tests/integration/test_merger.py`.
- [ ] **Action**: Update test to load `02_transcribed` JSONs from fixtures and assert output matches `03_merged`.
- [ ] **Refactor**: If test fails, update `src/minutia/steps/transcript_merger.py` to match the overlap logic from the notebook.

---

## Phase 3: Orchestrator Hardening
**Objective**: Wire up the new features in the Pipeline.

### 3.1 Update Configuration
- [ ] **Edit**: `src/minutia/pipeline/orchestrator.py` -> `PipelineConfig`.
- [ ] **Add Fields**:
    - `long_summary: bool`
    - `generate_markdown: bool`
    - `personal_notes: List[str]`
    - `soul_override: Optional[str]`

### 3.2 Update Execution Logic
- [ ] **Edit**: `src/minutia/pipeline/orchestrator.py` -> `_build_default_steps`.
- [ ] **Update**: `summarize` runner to use `generate_long_summary` if `config.long_summary` is True.
- [ ] **Add Step**: `report` runner (enabled if `config.generate_markdown` is True). Calls `create_markdown_report`.

### 3.3 End-to-End Validation
- [ ] **Create**: `tests/slow/test_e2e_refactor.py`.
- [ ] **Logic**: Run `PipelineOrchestrator` on `tests/fixtures/scenarios/microphone_only/input.mkv`.
- [ ] **Assert**: Check that `summary.txt` and `*.md` files are created in the run folder.

### 3.4 Delete Baseline
- [ ] **Delete**: `src/minutia/baseline_pipeline.py`.
- [ ] **Verify**: Grep codebase for `baseline_pipeline` to ensure no lingering imports.

---

## Phase 4: Dynamic Prompting (The "Soul")
**Objective**: Enable user personality overrides.

### 4.1 Config Discovery
- [ ] **Edit**: `src/minutia/config.py`.
- [ ] **Implement**: `load_overrides(config_dir: Path) -> dict`.
    - Read `SOUL.md` -> `soul_override`.
    - Read `HEARTBEAT.md` -> `heartbeat_override`.
    - Read `NOTES.json` -> `personal_notes`.

### 4.2 Inject Prompts
- [ ] **Edit**: `src/minutia/steps/summarize_transcript.py`.
- [ ] **Update**: `create_summary_prompt` (or system prompt builder).
- [ ] **Logic**:
    - If `soul_override`: Prepend to system prompt.
    - If `heartbeat_override`: Append formatting rules.
    - If `personal_notes`: Format as list and inject into context.
