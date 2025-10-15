# Guidance for Automated Agents

This repository uses the `uv` Python toolchain and a Makefile-driven workflow. Use this guide when planning or executing automated changes so that contributions stay consistent with the project's expectations.

## Core Context
- Primary goal: evolve the Minutia CLI that ingests OBS recordings, extracts audio, transcribes with Whisper, and summarizes with Claude.

- Reference materials: `design/design.md` (architecture), `TASKS-TODO.md` (priorities), and `README.md` (public overview).
- Python version: 3.10+. Formatting and linting are enforced via Ruff; line length is 88 characters.

## Environment Setup
- Install and sync dependencies with `uv`:
  - `uv sync` (base)
  - `uv sync --extra dev` for full developer tooling
- Prefer `make` targets for repeatable workflows (`make help` lists available tasks).
- Keep virtual environment artifacts out of the repo. `uv` manages `.venv/` automatically.

## Command Cheatsheet
- `make install` / `uv sync`: install base dependencies.
- `make install-dev`: install dev extras.
- `make lint` or `uv run ruff check .`: lint code.
- `make format` or `uv run ruff format .`: format code.
- `make test` or `uv run pytest`: run tests (add tests under `tests/` as pytest modules).
- `uv run minutia <command>`: execute CLI entry points defined in the project.

## Code Contributions
- Keep changes aligned with the architecture in `design/design.md`; update design docs if plans change.
- Favor small, composable modules inside `src/minutia/`. Maintain clear boundaries between pipeline stages (extraction, transcription, merging, summarization).
- Add or update tests whenever behavior changes. Default to unit tests; add integration coverage for pipeline interactions.
- Document new commands or behaviors in `README.md` and update internal guides when necessary.

## Quality and Verification
- Run `make lint-codex` and `make test-codex` (or their `uv` equivalents) before finalizing changes.
- For AI/LLM integrations or external API calls, provide mockable interfaces so tests remain deterministic.
- When modifying notebooks, mirror critical changes in the CLI implementation to avoid divergence.

## Working Etiquette for Agents
- Do not discard or overwrite user-maintained files. If manual edits exist, adapt around them.
- Explain non-obvious code with short comments; avoid redundant commentary.
- If external documentation is required, prefer official sources (see dependency links in `CLAUDE.md`).
- Surface assumptions or unresolved questions in your final summary so human collaborators can follow up.

Following this guidance keeps automated contributions predictable and easy to review within a typical `uv` Python project workflow.
