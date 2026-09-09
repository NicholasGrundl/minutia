# Decisions Log

## 2026-02-18: Project Reorganization
- **Decision**: Adopt the `_blueprint/` top-level structure for all planning and context documents.
- **Rationale**: To centralize "source of truth" files away from the `src/` and `tests/` directories, making the codebase cleaner and planning more visible.
- **Impact**: Moved `AGENTS.md`, `CLAUDE.md`, `TASKS-TODO.md`, and the `planning/` directory into `_blueprint/`.

## 2026-02-18: Production Stability
- **Decision**: Created `notebooks/PRODUCTION_Summary_Generator.ipynb` as a frozen copy of the fixture notebook.
- **Rationale**: Allow the user to continue generating production summaries using the known-good notebook while the CLI and core libraries are undergoing major refactoring and testing.
