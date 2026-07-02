# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, etc.) working in this repository.
It is the **canonical** instructions file — `CLAUDE.md` is a symlink to it (per the `_snap`
convention: `AGENTS.md` canonical, `CLAUDE.md`/`GEMINI.md` symlinks).

## Project Overview

Minutia is a meeting recording, transcription, and summarization tool. It extracts audio tracks
from OBS-recorded MKV files, transcribes them using Whisper, merges the transcripts
chronologically, and generates AI-powered summaries using Anthropic Claude.

**Current status**: mid-refactor from a Jupyter-notebook-driven workflow into a structured CLI
application. The active plan, task checklist, and current progress live in
`_snap/features/[active]refactor_to_cli.md` — read that (not this file) for what's actually
done vs. pending. The production notebook pipeline (`notebooks/CreateTranscriptProd.ipynb`,
frozen as `notebooks/PRODUCTION_Summary_Generator.ipynb`) still works and remains the fallback
until the CLI refactor reaches parity.

## Planning & session memory: `_snap/`

This repo's roadmap, feature specs, decision history, and reusable skills live in `_snap/` —
see [`_snap/AGENTS.md`](./_snap/AGENTS.md) for the full system. In short:
- **`_snap/ROADMAP.md`** — ordered list of features to build (the *future*)
- **`_snap/SESSION.md`** — current session's ephemeral scratchpad (the *present*)
- **`_snap/DECISIONS.md`** — append-only log of what was done and why (the *past*)
- **`_snap/features/`** — one spec per feature, e.g. `[active]refactor_to_cli.md`
- **`_snap/context/`** — reference docs per topic (ffmpeg, pytest, anthropic, whisper, etc.)
- **`_snap/skills/`** — activated into `.claude/skills/` as `/snap`, `/snap-git`,
  `/snap-script`, `/snap-search`, `/snap-wiki`

There is no separate `design/design.md` or `TASKS-TODO.md` at repo root — that content now
lives in `_snap/features/` and `_snap/ROADMAP.md` respectively.

## Project Dependencies & Documentation

**IMPORTANT**: When working with any package or library, **always consult the official
documentation FIRST** before making implementation decisions. Use the links below to fetch
current API information and best practices; deeper reference material for these is also
cached per-topic under `_snap/context/`.

### Core Dependencies

- **click** - CLI framework with advanced context/group features
  - 📚 Docs: https://click.palletsprojects.com/en/stable/api/
- **pydantic** - Data validation and models
  - 📚 Docs: https://ai.pydantic.dev/llms.txt
- **pydantic-settings** - Configuration management (env vars, .env files, CLI args)
  - 📚 Docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **rich** - Terminal UI, progress bars, formatted output
  - 📚 Docs: https://rich.readthedocs.io/en/latest/
- **anthropic** - Claude AI API client
  - 📚 API Docs: https://docs.claude.com/en/api/messages
  - 📚 SDK Reference: https://github.com/anthropics/anthropic-sdk-python/blob/main/api.md
- **openai-whisper** - Audio transcription
- **ffmpeg-python** - Audio/video processing

### Development Tools

- **uv** - Extremely fast Python package and project manager (written in Rust)
  - 📚 Main Docs: https://docs.astral.sh/uv/
  - 📚 Project Guide: https://docs.astral.sh/uv/guides/projects/
  - 📚 Configuration: https://docs.astral.sh/uv/concepts/projects/config/
- **ruff** - Fast linter/formatter (replaces black + flake8)
- **pytest** - Testing framework
  - 📚 How-to Guides: https://docs.pytest.org/en/stable/how-to/index.html#how-to-guides
  - 📚 API Reference: https://docs.pytest.org/en/stable/reference/index.html
- **mypy** - Type checking (optional, future enhancement)

### Optional Providers (Future)

- **ollama** - Local LLM integration for summarization
- **requests** - HTTP client for additional API integrations

### Documentation Best Practices

1. **ALWAYS check official docs FIRST** before implementing features or debugging issues.
2. **Fetch docs when uncertain** — use WebFetch to get the latest documentation.
3. **Add new docs to `_snap/context/`** as a new topic subfolder when you find helpful
   documentation for a package not already covered.
4. **Prefer official sources** — official documentation > blog posts > Stack Overflow.

## Development Commands

The project uses **UV** for package management and **Make** for task running.

```bash
# Package management
make install              # or: uv sync
make install-dev          # or: uv sync --extra dev
make install-all          # or: uv sync --extra dev --extra jupyter --extra media
make create-env-file      # scaffold a .env template

# Code quality
make lint                 # or: uv run ruff check .
make lint-fix             # or: uv run ruff check --fix .
make format                # or: uv run ruff format .
make check-all             # lint-fix + format + test (chained)

# Testing
make test                  # or: uv run pytest
make test-unit              # or: uv run pytest -m unit
make test-integration        # or: uv run pytest -m "unit or integration"
make test-all                # or: uv run pytest -m "unit or integration or slow"
make test-cov                 # or: uv run pytest --cov=src/minutia --cov-report=html --cov-report=term

# Sandboxed environments (e.g. Codex) where `uv run` hits permission issues
make test-codex               # runs pytest via .venv/bin/python directly
make lint-codex                # runs ruff via .venv/bin/python directly

# Development environment
make jupyter                # or: uv run jupyter lab --autoreload
make clean                  # clean build artifacts
uv run minutia --help       # run CLI commands
```

**Note**: `make commit` currently shells out to `.claude/hooks/macro-commit.sh --force`, which
no longer exists (archived at `_snap/archive/old_claude_stuff/hooks/macro-commit.sh`) — this
target is broken until it's either restored or repointed at the `_snap` git workflow
(`/snap-git`). See `opensource_polishing.md` for tracking.

### CLI Commands

```bash
# Extract audio from MKV
minutia extract-audio INPUT.mkv OUTPUT_DIR [--mic-track 3] [--desktop-track 2]

# Transcribe audio files
minutia transcribe MIC_AUDIO.wav DESKTOP_AUDIO.wav OUTPUT_DIR

# Merge transcripts
minutia merge-transcripts MIC_TRANSCRIPT.txt DESKTOP_TRANSCRIPT.txt OUTPUT.json

# Generate summary
minutia summarize MERGED_TRANSCRIPT.json OUTPUT.txt [--model claude-3-5-sonnet] [--dry-run]

# Complete pipeline (all steps)
minutia process-all INPUT.mkv OUTPUT_DIR [--mic-track 3] [--desktop-track 2] [--model claude-3-5-sonnet]
```

**Default track numbers**: OBS recordings typically use track 3 for microphone and track 2 for
desktop audio (1-indexed).

## Architecture

### Current `src/minutia/` layout

```
src/minutia/
├── cli.py                      # Click-based CLI entry point
├── config.py                   # Configuration loading
├── logging.py                  # Loguru setup
├── paths.py                    # RunPaths — path/output management
├── run_metadata.py             # Run metadata tracking
├── prompts.py                  # Summarization prompt templates
├── baseline_pipeline.py        # Standalone script version (pre-orchestrator); still the
│                                # documented entry point in README.md — do not delete until
│                                # steps/ has full parity (see refactor_to_cli spec)
├── legacy/                     # Isolated Jupyter-widget-era code (not used by the CLI)
│   ├── ui_jupyter.py
│   ├── claude_audio_widget.py
│   └── gpt_audio_widget.py
├── pipeline/
│   └── orchestrator.py         # PipelineOrchestrator — step coordination
├── clients/                    # AI/model client wrappers (in progress)
└── steps/                      # One module per pipeline stage
    ├── video_extraction.py     # FFmpeg operations only — no ML/AI dependencies
    ├── audio_transcription.py  # Whisper transcription only
    ├── transcript_merger.py    # Chronological merging logic
    └── summarize_transcript.py # Anthropic API integration
```

**Reference notebooks** (being migrated away from, kept for now):
- `notebooks/CreateTranscriptProd.ipynb` — original production pipeline
- `notebooks/PRODUCTION_Summary_Generator.ipynb` — frozen copy, current production fallback
- Other `notebooks/*.ipynb` — dev/eval scratch work

See `_snap/features/[active]refactor_to_cli.md` for the target architecture and current
migration progress.

## Code Organization Patterns

### Module Boundaries

Each module has a clear single responsibility:
- **`steps/video_extraction.py`**: FFmpeg operations only — no ML/AI dependencies
- **`steps/audio_transcription.py`**: Whisper transcription only
- **`steps/transcript_merger.py`**: Chronological merging logic
- **`steps/summarize_transcript.py`**: Anthropic API integration
- **`pipeline/orchestrator.py`**: Step coordination and progress reporting
- **`cli.py`**: Command orchestration and user interaction

### Audio Track Handling

OBS records with 1-indexed track numbers:
- Track 1: Usually video
- Track 2: Typically desktop/system audio
- Track 3: Typically microphone audio

The track-identification logic uses regex pattern matching (`track_(\d+)`) to map extracted
files to their original track numbers.

### Transcript Data Flow

1. **Video → Audio**: MKV extracted to separate WAV files per track
2. **Audio → Text**: Whisper produces timestamped segments per audio file
3. **Text → Merged**: Segments from both tracks sorted chronologically with source labels
4. **Merged → Summary**: Anthropic Claude generates a structured meeting summary

Transcripts use JSON-structured data with metadata (see `_snap/features/[active]refactor_to_cli.md`
for the current schema).

## Configuration & Secrets

### Environment Variables

Required for full pipeline:
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required for summarization
```

Optional (for future features):
```bash
OPENAI_API_KEY=sk-...            # Not currently used in CLI
```

### Configuration Precedence (Future)

```
CLI flags > Environment variables > Config file > Hard-coded defaults
```

Config file locations (searched in order): `.minutia` (project-specific), `.env` (standard env
file), `~/.minutia` (user global).

**Never commit `.env` or real API keys.** `.gitignore` already excludes `.env*`.

## AI-Assisted Workflow: `_snap` Skills

The project uses the `_snap` skill system (activated in `.claude/skills/`) for planning and
session workflows instead of the older, retired `.claude/commands/` slash-command convention:

- **`/snap`** — router: PLAN / BUILD / ALIGN a feature (interviews you, writes/updates specs
  in `_snap/features/`, updates `_snap/ROADMAP.md`)
- **`/snap-git`** — composes `[MACRO]` checkpoint commit messages from the working tree
- **`/snap-script`** — authors PEP 723 single-file `uv run` scripts
- **`/snap-search`** — filesystem exploration via `tree` before making changes
- **`/snap-wiki`** — fetch reference material into `_snap/context/`

The prior `align-design` / `begin-tasks` / `commit-progress` / `macro-commit` slash commands
are retired and archived at `_snap/archive/old_claude_stuff/`.

## Testing Strategy

Three-tier approach, already implemented under `tests/`:
- **Unit** (`tests/unit/`, fast, < 1s each): mocked dependencies, individual functions
- **Integration** (`tests/integration/`, medium, < 30s): real FFmpeg, real Whisper (tiny/base
  model), mocked Anthropic API
- **Slow** (`tests/slow/`, full pipeline): end-to-end with real models and API calls

```bash
pytest -m unit                          # Fast feedback loop
pytest -m "unit or integration"         # Pre-commit validation
pytest -m "unit or integration or slow" # Full validation (CI/nightly)
```

### Fixtures & mocking

- Shared fixtures live in `tests/conftest.py` (and per-tier `conftest.py` files).
- Golden-sample fixtures live in `tests/fixtures/scenarios/{scenario}/` — real input/output
  sets generated from the trusted notebook pipeline (see `refactor_to_cli` spec, "Golden
  Sample" methodology).
- Prefer the `mocker` fixture (from `pytest-mock`) over `unittest.mock.patch`.
- Use `monkeypatch` only for simple environment-variable or attribute overrides.
- Complex mocks (e.g. LLM responses, Whisper, FFmpeg) live in `tests/mocks/` — check there
  before writing a new one.
- **Anthropic API**: always mock in unit/integration tests to avoid real costs.

## Working with the Codebase

### Adding New Features

1. Check `_snap/ROADMAP.md` and the relevant `_snap/features/*.md` spec first.
2. If a feature needs planning, use `/snap` rather than starting ad hoc.
3. Always add tests (or at minimum, manual testing steps).
4. Update CLI help text and this file as needed.

### Debugging Pipeline Issues

Each pipeline stage logs via loguru:
- **video_extraction**: FFmpeg operations and track identification
- **audio_transcription**: Whisper model loading and transcription progress
- **transcript_merger**: Segment merging and overlap detection
- **summarize_transcript**: Token estimation and API calls

### Working Etiquette for Agents

- Do not discard or overwrite user-maintained files; if manual edits exist, adapt around them.
- Explain non-obvious code with short comments; avoid redundant commentary.
- If external documentation is required, prefer official sources (links above), and cache
  useful finds into `_snap/context/`.
- Surface assumptions or unresolved questions in your final summary so the user can follow up.
- Per `_snap` convention: every `mv`/`git mv` is a separate, individually-approved,
  individually-committed operation — never bundled with content edits.

### Common Development Workflows

```bash
# Extract and transcribe a recording, step by step
uv run minutia extract-audio recording.mkv ./output/
uv run minutia transcribe ./output/microphone_audio.wav ./output/desktop_audio.wav ./output/
uv run minutia merge-transcripts ./output/microphone_transcript.txt ./output/desktop_transcript.txt ./output/merged.json
uv run minutia summarize ./output/merged.json ./output/summary.txt

# Full pipeline in one command
uv run minutia process-all recording.mkv ./output/

# Development iteration cycle
make lint-fix
make format
make test
uv run minutia <command>
```

## Code Quality Standards

- **Line length**: 88 characters (configured in `pyproject.toml`)
- **Linter**: ruff (pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade)
- **Formatter**: ruff format (double quotes, space indentation)
- **Python version**: >= 3.12 (per `pyproject.toml`; some legacy artifacts reference 3.10+)

## Known Issues

See `_snap/ROADMAP.md` ("Known issues") and `_snap/features/[active]refactor_to_cli.md`
("Known Issues") for the current list — currently just the FFmpeg output-overwrite handling in
`video_extraction.py`, not yet re-verified against current code.

## Dependencies & Performance

Heavy ML/AI dependencies: **torch** (Whisper execution, GPU/CPU), **transformers**,
**whisper**, **anthropic**. First Whisper model load is slow; transcription time scales with
audio duration (roughly real-time on CPU); GPU acceleration used if CUDA is detected.
