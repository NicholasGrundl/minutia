# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, etc.) working in this repository.
It is the **canonical** instructions file — `CLAUDE.md` is a pointer to it.

## Project Overview

Minutia is a meeting recording, transcription, and summarization tool. It extracts audio tracks
from OBS-recorded MKV files, transcribes them using Whisper, merges the transcripts
chronologically, and generates AI-powered summaries using Anthropic Claude.

**Current status**: the `minutia` CLI is the daily driver (the wizard plus `run` / `info` /
`setup`). A pre-CLI standalone script (`baseline_pipeline.py`) and the `PipelineOrchestrator`
remain in the tree but are off the CLI path and scheduled for removal.

## Planning docs

The roadmap, feature specs and decision history are kept outside this repo; nothing in the tree
depends on them. `[MACRO]` commits in the history mark task and feature checkpoints
(`git log --grep '\[MACRO\]'`).

## Project Dependencies & Documentation

**IMPORTANT**: When working with any package or library, **always consult the official
documentation FIRST** before making implementation decisions. Use the links below to fetch
current API information and best practices.

### Core Dependencies

- **typer** - CLI framework (built on click; type-hint-driven commands)
  - 📚 Docs: https://typer.tiangolo.com/
  - Note: `click` remains available as typer's dependency (used for
    `ClickException` and `click.testing.CliRunner`)
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
- **ty** - Type checking (`just ty`; pre-existing errors are baselined in `pyproject.toml`)
- **just** - Task runner (`just` with no arguments lists every recipe)

### Optional Providers (Future)

- **ollama** - Local LLM integration for summarization
- **requests** - HTTP client for additional API integrations

### Documentation Best Practices

1. **ALWAYS check official docs FIRST** before implementing features or debugging issues.
2. **Fetch docs when uncertain** — use WebFetch to get the latest documentation.
3. **Prefer official sources** — official documentation > blog posts > Stack Overflow.

## Development Commands

The project uses **uv** for package management and **just** as the task runner.

```bash
# Environment
just sync                 # or: uv sync (dev group + CUDA torch)
just sync-cpu             # or: uv sync --extra cpu (CPU-only torch; what CI installs)
just sync-all             # or: uv sync --all-groups
just create-env-file      # scaffold a .env template
just reinstall            # reinstall the minutia tool from GitHub main

# Code quality
just ruff                 # ruff format + ruff check --fix (mutating; src + tests)
just ty                   # or: uv run ty check (read-only)
just ci                   # ruff, then ty

# Testing
just test                 # or: uv run pytest (forwards args: just test -k merge)
just test-unit            # or: uv run pytest -m unit
just test-integration     # or: uv run pytest -m "unit or integration"
just test-all             # or: uv run pytest -m "unit or integration or slow"
just test-cov             # or: uv run pytest --cov=src/minutia --cov-report=html --cov-report=term

# Releases (bump, commit, tag, push; preview with: uv run python scripts/release.py patch -n)
just tag-patch            # also: tag-minor, tag-major

# Development environment
just jupyter              # or: uv run jupyter lab --autoreload
just clean                # remove build + test artifacts
uv run minutia --help     # run CLI commands
```

### CLI Commands

The CLI is a `cli/` subpackage (`src/minutia/cli/`) with a concise command tree. Bare `minutia`
is a full-screen **rich wizard** (`cli/wizard/`); execution lives under `run`, read-only
introspection under `info`, and first-run config under `setup`. Heavy imports (torch/whisper,
anthropic) are lazy, so `--help`/`--version`/`info`/`setup` stay cold-start cheap.

```bash
# Bare command = the interactive wizard. Self-determines: if the recordings folder + API key
# resolve it runs the guided pipeline; otherwise it walks setup first, then runs.
minutia

# First-run / re-run config wizard: persists recordings folder + Anthropic API key to the user
# config.env (chmod 600). Unconditional (runs even when already configured).
minutia setup

# Read-only introspection (no heavy imports)
minutia info                 # resolved settings + provenance (was `minutia config`)
minutia info config          # alias of bare `info`
minutia info recordings      # list the newest .mkv files in the recordings folder

# Run the whole pipeline non-interactively (INPUT optional when MINUTIA_RECORDINGS_DIR is set —
# newest recording; cost gate mirrors `run summarize`: prompt / --yes / --dry-run)
minutia run pipeline [INPUT.mkv] [OUTPUT_DIR] [--mic-track 3] [--desktop-track 2] \
    [--prompt-kind ...] [--notes NOTES.md] [--personal-info ME.md] [--model ...] \
    [--gpu/--no-gpu] [--force] [--dry-run] [--yes]

# Individual stages (each skips if outputs exist; --force to redo)
minutia run extract-audio [INPUT.mkv] [OUTPUT_DIR] [--mic-track 3] [--desktop-track 2] [--force]
minutia run transcribe MIC_AUDIO.wav DESKTOP_AUDIO.wav [OUTPUT_DIR] [--whisper-model medium.en] [--gpu/--no-gpu] [--force]
minutia run merge MIC_TRANSCRIPT.json DESKTOP_TRANSCRIPT.json OUTPUT.json
minutia run summarize MERGED_TRANSCRIPT.json [OUTPUT_DIR] \
    [--prompt-kind minutia|baseline|realtor|slide-review|interview-debrief|discovery-summary] \
    [--notes NOTES.md] [--personal-info ME.md] [--model claude-sonnet-4-6] [--dry-run] [--yes]

# --version is a top-level eager option
minutia --version
```

**Removed** (superseded): `minutia go` and `minutia process-all` → the wizard + `run pipeline`;
top-level `minutia config` → `minutia info`. The `PipelineOrchestrator` + `baseline_pipeline.py`
are no longer on the CLI path and are scheduled for removal.

**New deps**: `rich` (wizard rendering) + `python-yakh` (keystrokes).

**Default track numbers**: OBS recordings typically use track 3 for microphone and track 2 for
desktop audio (1-indexed).

## Architecture

### Current `src/minutia/` layout

```
src/minutia/
├── cli/                        # Typer CLI subpackage (entry point: minutia.cli:main)
│   ├── app.py                  # top-level app wiring + bare-wizard dispatch + --version
│   ├── run.py                  # `run` group: pipeline + the four stage subcommands
│   ├── setup.py                # `setup` command → the config wizard
│   ├── info.py                 # `info` group: settings/provenance, recordings listing
│   ├── _steps.py               # shared step helpers (heavy imports lazy inside them)
│   └── wizard/                 # full-screen rich wizard
│       ├── tui.py              # presentation chrome (rich + yakh), injectable for tests
│       └── flow.py             # setup + guided-run flows and their pure cores
├── config.py                   # Configuration loading + user-config writer (write_user_config)
├── logging.py                  # Loguru setup
├── paths.py                    # RunPaths — path/output management
├── run_metadata.py             # Run metadata tracking
├── prompts.py                  # Summarization prompt templates
├── baseline_pipeline.py        # Standalone script version (pre-orchestrator); documented in
│                                # README.md as the legacy fallback, off the CLI path
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

## Code Organization Patterns

### Module Boundaries

Each module has a clear single responsibility:
- **`steps/video_extraction.py`**: FFmpeg operations only — no ML/AI dependencies
- **`steps/audio_transcription.py`**: Whisper transcription only
- **`steps/transcript_merger.py`**: Chronological merging logic
- **`steps/summarize_transcript.py`**: Anthropic API integration
- **`pipeline/orchestrator.py`**: Step coordination and progress reporting
- **`cli/`**: Command orchestration and user interaction (the wizard, `run`/`info`/`setup`)

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

Transcripts use JSON-structured data with metadata; `steps/transcript_merger.py` defines the
merged schema.

## Configuration & Secrets

### Environment Variables

Required for full pipeline:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # Required for summarization
```

Optional (all `MINUTIA_`-prefixed):
```bash
MINUTIA_RECORDINGS_DIR=~/Videos   # Where OBS drops MKVs; the wizard + `minutia run pipeline`
                                  # browse it (newest .mkv when no input is given)
MINUTIA_OUTPUT_DIR=...            # Artifact home; defaults to ~/Documents/minutia (platformdirs)
MINUTIA_WHISPER_MODEL=medium.en   # Whisper model (default: base)
MINUTIA_SUMMARY_MODEL=...         # Summarization model
MINUTIA_PERSONAL_INFO=...         # Path to a personal-info file for prompts
MINUTIA_LOG_LEVEL=INFO
```

### Configuration Precedence

```
CLI flags > Environment variables > contextual .env > user config > platformdirs defaults
```

The user-global config is an env-format file at `platformdirs.user_config_path("minutia")/config.env`
(e.g. `~/.config/minutia/config.env` on Linux). Minutia discovers the nearest `.env` from the
invocation directory, stopping at the first `.git`/`pyproject.toml` project boundary and before the
user's home directory. Use global `--env-file PATH` to select one explicitly or `--no-env-file` to
disable contextual discovery. Input and output paths do not affect discovery. Run **`minutia
info`** to print every resolved value and which layer supplied it.

Relative paths in the user config and contextual `.env` are anchored to the file that declares
them. Relative process-environment and CLI paths are anchored to the invocation directory.

**Never commit `.env` or real API keys.** `.gitignore` already excludes `.env*`.

## Testing Strategy

**Always run tests through `uv`** — either `just test` (which shells out to `uv run pytest`) or
`uv run pytest ...` directly. Do **not** invoke the interpreter under `.venv/` (e.g.
`.venv/bin/python -m pytest`); that bypasses `uv`'s environment resolution and can run against a
stale or mismatched dependency set. Examples:

```bash
just test                       # full suite via uv run pytest (forwards args: just test -k merge)
uv run pytest -m unit            # a marker subset
uv run pytest path::to::test -q  # a single test
```

Three-tier approach, already implemented under `tests/`:
- **Unit** (`tests/unit/`, fast, < 1s each): mocked dependencies, individual functions
- **Integration** (`tests/integration/`, medium, < 30s): real FFmpeg, real Whisper (tiny/base
  model), mocked Anthropic API
- **Slow** (`tests/slow/`, full pipeline): end-to-end with real models and API calls

```bash
pytest -m unit                          # Fast feedback loop
pytest -m "unit or integration"         # Pre-commit validation
pytest -m "unit or integration or slow" # Full validation (local)
```

### Fixtures & mocking

- Shared fixtures live in `tests/conftest.py` (and per-tier `conftest.py` files).
- Golden-sample fixtures live in `tests/fixtures/scenarios/{scenario}/` — real input/output
  sets generated from the trusted notebook pipeline.
- Prefer the `mocker` fixture (from `pytest-mock`) over `unittest.mock.patch`.
- Use `monkeypatch` only for simple environment-variable or attribute overrides.
- Complex mocks (e.g. LLM responses, Whisper, FFmpeg) live in `tests/mocks/` — check there
  before writing a new one.
- **Anthropic API**: always mock in unit/integration tests to avoid real costs.

## Working with the Codebase

### Adding New Features

1. Always add tests (or at minimum, manual testing steps).
2. Update CLI help text and this file as needed.

### Debugging Pipeline Issues

Each pipeline stage logs via loguru:
- **video_extraction**: FFmpeg operations and track identification
- **audio_transcription**: Whisper model loading and transcription progress
- **transcript_merger**: Segment merging and overlap detection
- **summarize_transcript**: Token estimation and API calls

### Working Etiquette for Agents

- Do not discard or overwrite user-maintained files; if manual edits exist, adapt around them.
- Explain non-obvious code with short comments; avoid redundant commentary.
- If external documentation is required, prefer official sources (links above).
- Surface assumptions or unresolved questions in your final summary so the user can follow up.
- Every `mv`/`git mv` is a separate, individually-approved, individually-committed
  operation — never bundled with content edits.

### Common Development Workflows

```bash
# Extract and transcribe a recording, step by step
uv run minutia run extract-audio recording.mkv ./output/
uv run minutia run transcribe ./output/microphone_audio.wav ./output/desktop_audio.wav ./output/
uv run minutia run merge ./output/microphone_transcript.json ./output/desktop_transcript.json ./output/merged.json
uv run minutia run summarize ./output/merged.json ./output/

# Full pipeline in one command
uv run minutia run pipeline recording.mkv ./output/

# Development iteration cycle
just ruff
just ty
just test
uv run minutia <command>
```

## Code Quality Standards

- **Line length**: 88 characters (configured in `pyproject.toml`)
- **Linter**: ruff (pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade)
- **Formatter**: ruff format (double quotes, space indentation)
- **Python version**: >= 3.12, < 3.14 (per `pyproject.toml`; `.python-version` pins 3.12)

## Known Issues

- **`ty` baseline**: pre-existing type errors are baselined per file and per rule via
  `[[tool.ty.overrides]]` in `pyproject.toml`; new errors elsewhere still fail `just ty`.
- **Unknown summary model**: `steps/summarize_transcript.py` looks a model up with
  `anthropic_models.get(model_name)["name"]`, which fails with a `TypeError` for a model name
  that is not in the registry.

## Dependencies & Performance

Heavy ML/AI dependencies: **torch** (Whisper execution, GPU/CPU), **whisper**, **anthropic**. First Whisper model load is slow; transcription time scales with
audio duration (roughly real-time on CPU); GPU acceleration used if CUDA is detected.
