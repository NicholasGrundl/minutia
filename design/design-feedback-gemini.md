# Design & Implementation Feedback: Gemini Analysis

This document provides an analysis of the current state of the `src` and `tests` directories against the project goals outlined in `design/design.md` and `TASKS-TODO.md`.

## 1. Overall Summary

The project is in a transitional state, which is consistent with the phased approach in the TODO list. Core architectural components from the design document, such as `RunPaths` and the `PipelineOrchestrator`, have been implemented and are well-tested at a unit level.

However, the current implementation has **two parallel pipelines**:
1.  A **legacy pipeline** (`baseline_pipeline.py`) which is a direct script conversion of the original notebook.
2.  A **new, orchestrated pipeline** (`pipeline.py`) that reflects the target architecture.

The current CLI (`cli.py`) is wired to the legacy pipeline, bypassing the new orchestrator entirely. This is the most significant point of deviation from the target design, though it aligns with the phased implementation plan where core components are built first before being integrated.

The quality of the new code and its unit tests is high. The main gaps are in integration, adoption of the new architecture, and implementation of supporting features like logging and the rich CLI.

## 2. Architecture & Design Adherence

This section focuses on discrepancies between the current code in `src/` and the target architecture in `design/design.md`.

### 🔴 Major Deviations

*   **Pipeline Orchestration Not Used**: `src/minutia/cli.py` and `src/minutia/baseline_pipeline.py` represent the primary entry points, but neither uses the new `PipelineOrchestrator`. They call modules like `video_extraction` and `audio_transcription` directly. The new, well-designed `PipelineOrchestrator` is effectively unused in the current end-to-end workflow.
*   **Flat Source Layout**: The `src/minutia/` directory is flat. The design document proposes a more organized structure with sub-packages like `steps/`, `clients/`, and `pipeline/`. The current structure makes it harder to distinguish between core orchestration, data models, and individual pipeline steps.
*   **Basic CLI**: The current CLI in `src/minutia/cli.py` is a functional but basic `click` interface. It does not implement the `rich`-based progress bars, status panels, or sophisticated UX flows described in the design document. This is expected, as it is marked as a "Post-MVP" task (Phase 7).

### 🟡 Minor & Expected Deviations

*   **Legacy Data Formats**: `audio_transcription.py` still writes intermediate transcripts as plain `.txt` files. The design specifies moving to a structured JSON format. This is noted as a "Post-MVP" task (Phase 6), so this deviation is expected at this stage.
*   **Standard Logging**: The code uses Python's built-in `logging` module. The design specifies a unified `loguru` setup with contextual fields. This is an unimplemented "MVP" task (Phase 4).
*   **No Configuration System**: There is no centralized configuration system as designed. The `baseline_pipeline.py` uses `argparse` and `dotenv`, while the new architecture has no configuration loader yet. This is an unimplemented "MVP" task (Phase 4).

### 🟢 Good Alignment

*   **Path Management (`paths.py`)**: The `RunPaths` dataclass in `src/minutia/paths.py` is an excellent implementation that closely matches the design specification. It correctly handles path resolution, collision, and provides the specified factory methods.
*   **Pipeline Models (`pipeline.py`)**: The data structures like `PipelineConfig`, `PipelineResult`, and `StepProgress` are implemented as designed and provide a solid foundation for the orchestrator.

## 3. Test Quality & Coverage

The quality of the unit tests for the *new* architectural components is high. They are not "junior dev" work; they are focused, sensible, and correctly isolate components for testing.

### ✅ Strengths

*   **`tests/test_paths.py`**: Provides excellent, thorough unit tests for the `RunPaths` logic, covering creation, collision handling, and cleanup.
*   **`tests/test_pipeline_models.py`**: Contains good validation for the core data classes of the pipeline.
*   **`tests/test_pipeline_orchestrator.py`**: Effectively unit-tests the orchestrator's logic, including step execution, failure handling, and skipping disabled steps.

### ❌ Gaps & Weaknesses

*   **No Integration Testing for New Orchestrator**: The most critical testing gap is the absence of an integration test for the `PipelineOrchestrator`. The existing smoke test, `tests/test_baseline_pipeline.py`, covers the *old* `baseline_pipeline.py` script using heavy mocking. There is **no test that verifies the new orchestrator can successfully run the actual pipeline steps together.**
*   **No Test Categories**: The tests do not use the `unit`, `integration`, and `slow` markers proposed in the design document. This makes it difficult to run different test suites based on speed and resource requirements.
*   **Unrelated UI Code**: The `src/minutia` directory contains files like `claude_audio_widget.py`, `gpt_audio_widget.py`, and `ui_jupyter.py`. These appear to be remnants from notebook-based experimentation and are not part of the CLI application design. They add clutter and are not covered by tests.

## 4. Recommendations

1.  **Prioritize Orchestrator Integration**: The immediate priority should be to refactor `cli.py` and/or `baseline_pipeline.py` to use the new `PipelineOrchestrator`. This will unify the codebase around the target architecture.
2.  **Create an Integration Test**: Before or alongside the integration, create a true integration test for the `PipelineOrchestrator`. This test should run the full pipeline (from video to summary) using the real step implementations with minimal mocking (e.g., mocking API calls but not filesystem interactions). This will provide confidence that the new architecture actually works end-to-end.
3.  **Refactor Source Layout**: Once the orchestrator is integrated, refactor the `src/minutia/` directory to match the `steps/`, `clients/`, `pipeline/` structure from the design document. This will improve clarity and maintainability.
4.  **Implement Test Categories**: Add `pytest` markers (`@pytest.mark.unit`, `@pytest.mark.integration`) to the existing tests to align with the testing strategy in the design document.
5.  **Cleanup Unused UI Code**: Move the Jupyter/Panel widget files (`claude_audio_widget.py`, etc.) to a separate `notebooks/` or `experimental/` directory to keep the `src` folder focused on the CLI application.
