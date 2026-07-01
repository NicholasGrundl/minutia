# Refactor Status Report: Minutia Project Audit (Feb 2026)

## Overview
This report documents the findings from an audit of the Minutia codebase. The project was left in a "half-migrated" state during a transition from Jupyter Notebooks to a structured CLI package.

## 1. Technical Debt & Logic Fragmentation
- **The "Baseline" Ghost**: `src/minutia/baseline_pipeline.py` contains advanced features (Long Summaries with token continuation, AI-driven filename generation for Markdown) that were never ported to the `PipelineOrchestrator`.
- **Duplicate Execution Paths**: Currently, the CLI `process_all` command uses the `Orchestrator`, while other scripts might still rely on the `baseline_pipeline`.
- **Step Stubs**: Some steps in `src/minutia/steps/` are missing the production-grade logic found in the original `CreateTranscriptProd` notebook.

## 2. Package Plumbing Issues
- **Entry Point Failure**: `pyproject.toml` defines `minutia = "minutia:main"`, but `src/minutia/__init__.py` points to a `cli` group that isn't wrapped in a standard `main()` function. This prevents `uv run minutia` from working correctly.
- **Dependency Bloat**: `pyproject.toml` contains many Jupyter-specific dependencies (`ipywidgets`, `panel`) mixed into optional groups, but some core modules (`ui_jupyter.py`) still import them, creating hard dependencies in a "CLI" package.

## 3. Test Infrastructure State
- **Scattered Tests**: Existing tests (`test_paths.py`, `test_pipeline_orchestrator.py`) are located in the `tests/` root, ignoring the planned `unit/`, `integration/`, and `slow/` hierarchy.
- **Fixture Mismatch**: The project has excellent "Golden Samples" and scenario fixtures in `tests/fixtures/scenarios/`, but the current test suite does not use them for regression testing.

## 4. Legacy Clutter
- **Jupyter Widgets**: `claude_audio_widget.py` and `gpt_audio_widget.py` are located in the core `src/minutia/` directory. These are legacy UI components that should be isolated from the CLI logic.
- **Stale Metadata**: `run_metadata.py` is present but needs to be unified with the `ProcessingResult` model defined in the design docs.

## 5. Summary Step Deficiencies
- **Continuation Logic**: The current `orchestrator` summarization step cannot handle transcripts that exceed the single-pass token limit.
- **Prompt Isolation**: System prompts are hardcoded in `summarize_transcript.py` and do not support the "SOUL/HEARTBEAT" override patterns found in more mature implementations.
