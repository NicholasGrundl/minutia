# Test Suite Audit - minutia

## Overview
The `minutia` test suite is well-structured and follows modern testing practices (behavioral testing, rich fixtures, extensive mocking). It prioritizes an "offline-first" approach, allowing the suite to run without external dependencies (GPU, API keys).

## High-Signal Tests
- **`tests/unit/test_paths.py`**: Ensures the integrity of the run directory structure and cleanup policies.
- **`tests/unit/test_pipeline_orchestrator.py`**: Validates the core logic of pipeline execution, step sequencing, and error handling.
- **`tests/integration/test_baseline_pipeline.py`**: A robust smoke test for the entire pipeline.
- **`tests/integration/test_cli_process_all.py`**: Verifies that the CLI correctly bridges to the pipeline orchestrator.
- **`tests/mocks/`**: Provides excellent infrastructure for deterministic, fast tests.

## Brittle or Low-Value Areas
- **`tests/conftest.py`**: Contains some potentially stale references. For example, the `test_video_files` fixture expects a `fixtures/video` directory which does not exist in the current `fixtures/scenarios/` architecture.
- **`tests/red_test_stubs.py`**: Useful for TDD but currently floating and detached from the main suites. These should be moved to appropriate test files as their related features are implemented.
- **`tests/test_mocks_sanity.py`**: (Not deeply audited but likely a one-time verify) Should be kept minimal or moved to a maintenance suite.

## Missing Coverage (Identified in Spec)
- **Failure Mode Permutations**: We lack systematic tests for partial completion states (e.g., audio extracted but transcription failed) and specific environment errors (e.g., missing Anthropic key, FFmpeg track missing).
- **Test Classes for Complex Integration**: While functional tests are good for simple cases, complex integration scenarios (Phase 3) will benefit from `TestClass` structures for shared mock state.

## Recommendations
1. **Refactor `conftest.py`**: Align fixtures with the `fixtures/scenarios/` structure.
2. **Implement `TestE2EPermutations`**: Create a parameterised suite to cover the identified failure modes.
3. **Formalise Scenario Loading**: Enhance the `scenario_loader` logic to easily swap between different fixture scenarios.
4. **Cleanup**: Remove `red_test_stubs.py` once its contents are integrated.
