# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minutia is a meeting recording, transcription, and summarization tool. It extracts audio tracks from OBS-recorded MKV files, transcribes them using Whisper, merges the transcripts chronologically, and generates AI-powered summaries using Anthropic Claude.

**Current Status**: Early development. The project is in active refactoring from Jupyter notebooks to a structured CLI application. The production pipeline (CreateTranscriptProd.ipynb) is working but needs migration to the CLI structure outlined in design/design.md.

## Project Dependencies & Documentation

**IMPORTANT**: When working with any package or library, **always consult the official documentation FIRST** before making implementation decisions. Use the links below to fetch current API information and best practices.

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

**When working with dependencies:**

1. **ALWAYS check official docs FIRST** - Use the links above before implementing features or debugging issues
2. **Fetch docs when uncertain** - If you're not 100% certain about an API or pattern, use WebFetch to get the latest documentation
3. **Add new docs to this list** - When you find helpful documentation for a package not listed here, add it to this section
4. **Keep docs current** - This list should grow as the project expands and new dependencies are added
5. **Prefer official sources** - Official documentation > blog posts > Stack Overflow

**This list is a living document** - expand it as you discover authoritative documentation sources for the packages used in this project.

## Development Commands

The project uses **UV** for package management and task execution. All development scripts are defined in `[tool.uv.scripts]` in `pyproject.toml`. You can run them either way:
- **Make**: `make <target>` (convenient, traditional)
- **UV direct**: `uv run <script>` (explicit, portable)

For a complete list of commands, run: `make help`

### Package Management

```bash
# Install dependencies
make install              # or: uv sync
make install-dev          # or: uv sync --extra dev
make install-all          # or: uv sync --extra dev --extra jupyter --extra media

# Create .env file template
make create-env-file
```

### Code Quality

```bash
# Linting and formatting
make lint                 # or: uv run lint
make lint-fix             # or: uv run lint-fix
make format               # or: uv run format
make check-all            # or: uv run check-all  (runs lint-fix + format + test)
```

### Testing

```bash
# Run tests (when implemented)
make test                 # or: uv run test            (all tests)
make test-unit            # or: uv run test-unit       (unit only, fast)
make test-integration     # or: uv run test-integration (unit + integration)
make test-all             # or: uv run test-all        (includes slow tests)
make test-cov             # or: uv run test-cov        (with coverage report)
```

**Important**: Tests directory does not exist yet. When creating tests, place them in `tests/` following pytest conventions with markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`.

### Development Environment

```bash
# Start Jupyter Lab (for notebook development)
make jupyter              # or: uv run jupyter

# Clean build artifacts
make clean                # or: uv run clean

# Run CLI commands
uv run minutia --help
```

### CLI Commands

The CLI is organized into separate commands for each pipeline stage:

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

**Default Track Numbers**: OBS recordings typically use track 3 for microphone and track 2 for desktop audio (1-indexed).

## Architecture

### Current Structure (Transitional)

The codebase is in transition from Jupyter notebooks to a structured CLI application:

```
src/minutia/
├── cli.py                      # Click-based CLI interface (current entry point)
├── video_extraction.py         # FFmpeg-based audio extraction from MKV
├── audio_transcription.py      # Whisper-based transcription
├── transcript_merger.py        # Chronological merging of dual-track transcripts
└── summarize_transcript.py     # Anthropic Claude summarization
```

**Working Notebooks** (reference implementations):
- `CreateTranscriptProd.ipynb` - Production pipeline with all advanced features
- `CreateTranscript-Dev.ipynb` - Development/testing version
- `CreateTranscript-Evals.ipynb` - Evaluation and analysis

### Target Architecture (design/design.md)

The design document outlines a comprehensive refactoring plan with:
- **Pipeline orchestration** with state management and resume capability
- **Rich CLI** with progress bars and status panels
- **Unified logging** using loguru instead of basic logging
- **RunPaths abstraction** for consistent file handling
- **Test infrastructure** with unit/integration/slow test categories

**Key Migration Principle**: Preserve working functionality first, enhance second. Never break the existing pipeline during migration.

## Code Organization Patterns

### Import Issues (Critical Technical Debt)

**video_extraction.py has significant unused imports** that must be cleaned up:
- Lines 3-12 import whisper, pandas, numpy, transformers, torch, openai, anthropic, pydantic, instructor, dotenv
- **Only ffmpeg, os, logging, shutil, sys, re are actually used**
- These heavy dependencies slow imports and confuse module boundaries

When working on video_extraction.py, remove unused imports first.

### Module Boundaries

Each module has a clear single responsibility:
- **video_extraction.py**: FFmpeg operations only - no ML/AI dependencies
- **audio_transcription.py**: Whisper transcription only
- **transcript_merger.py**: Chronological merging logic
- **summarize_transcript.py**: Anthropic API integration
- **cli.py**: Command orchestration and user interaction

### Audio Track Handling

OBS records with 1-indexed track numbers:
- Track 1: Usually video
- Track 2: Typically desktop/system audio
- Track 3: Typically microphone audio

The `identify_audio_tracks()` function uses regex pattern matching (`track_(\d+)`) to map extracted files to their original track numbers.

### Transcript Data Flow

1. **Video → Audio**: MKV extracted to separate WAV files per track
2. **Audio → Text**: Whisper produces timestamped segments per audio file
3. **Text → Merged**: Segments from both tracks sorted chronologically with source labels
4. **Merged → Summary**: Anthropic Claude generates structured meeting summary

Current transcripts use bracketed timestamp format:
```
[0.00 - 2.00]  Hello everyone
[30.00 - 32.00]  (desktop) Background music playing
```

**Target format** (per design.md): JSON-structured transcripts with metadata for easier parsing and analysis.

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

Design document specifies:
```
CLI flags > Environment variables > Config file > Hard-coded defaults
```

Config file locations (searched in order):
1. `.minutia` (project-specific)
2. `.env` (standard env file)
3. `~/.minutia` (user global)

## Custom Slash Commands

The project includes custom Claude Code slash commands in `.claude/commands/`:

- **/macro-commit** - Consolidate recent [MICRO] commits into a [MACRO] summary commit
- **/align-design** - Align TASKS-TODO.md with design documentation through phased implementation
- **/begin-tasks** - Select and implement next logical task(s) from TASKS-TODO.md
- **/commit-progress** - Create structured [MACRO] commits for major structural changes

These commands use a [MICRO]/[MACRO] commit convention for tracking incremental vs. structural changes.

## Testing Strategy (When Implemented)

The design document specifies a three-tier testing approach:

### Test Categories
- **Unit tests** (fast, < 1s each): Mocked dependencies, test individual functions
- **Integration tests** (medium, < 30s): Real Whisper tiny model, real FFmpeg, mocked APIs
- **Slow tests** (full pipeline): End-to-end with actual models and API calls

### Running Tests
```bash
pytest -m unit                          # Fast feedback loop
pytest -m "unit or integration"         # Pre-commit validation
pytest -m "unit or integration or slow" # Full validation (CI/nightly)
```

### Fixture Strategy
- Session-scoped: Expensive resources like Whisper models, test audio files
- Module-scoped: Shared test data like sample transcripts
- Function-scoped: Isolated run directories for test independence

### Mocking Approach
- **Anthropic API**: Always mock in unit/integration tests to avoid costs
- **Whisper**: Mock for unit tests, use tiny model for integration tests
- **FFmpeg**: Use real FFmpeg with small test files for integration tests

## Important Development Notes

### Current Pipeline Verification

**Before making structural changes**, always verify the working pipeline:
1. Run `CreateTranscriptProd.ipynb` end-to-end with test recording
2. Confirm all outputs (transcripts, merged transcript, summary) are generated correctly
3. Document current behavior to ensure migration preserves functionality

### Migration Phases (from design.md)

**Phase 1**: Foundation & Verification (Critical Path)
- Verify notebook pipeline works
- Create standalone script version
- Add basic integration test

**Phase 2**: Pipeline Architecture (Core Focus)
- Implement PipelineOrchestrator with progress reporting
- Add state management and resume capability

**Phase 3**: Infrastructure Migration (Parallel to Phase 2)
- RunPaths dataclass for file management
- Unified loguru logging
- Centralized configuration

**Phase 4**: CLI Enhancement (Depends on 2-3)
- Rich progress bars and status panels
- Friendly error messages

### Code Quality Standards

- **Line length**: 88 characters (configured in pyproject.toml)
- **Linter**: ruff with pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade
- **Formatter**: ruff format (double quotes, space indentation)
- **Python version**: >= 3.10

### Known Issues (TASKS-TODO.md)

High-priority items to address:
1. **Import cleanup** in video_extraction.py (removes ~9 unused imports)
2. **Unused loop variable** `stream` on line 72 of video_extraction.py
3. **No test infrastructure** - tests/ directory doesn't exist yet
4. **Basic logging** needs migration to loguru for structured logging

## Design Documents

Critical reading for understanding the target architecture:

- **design/design.md** - Comprehensive MVP design with detailed API specifications
- **TASKS-TODO.md** - Current prioritized task list with technical debt items
- **planning/** - Historical planning documents and design iterations

The design document is the source of truth for the refactoring direction. When making architectural changes, ensure they align with the design patterns specified there.

## Dependencies & Performance

### Heavy Dependencies

The project has significant ML/AI dependencies:
- **torch** - PyTorch for Whisper model execution (GPU/CPU)
- **transformers** - Hugging Face transformers library
- **whisper** - OpenAI Whisper for transcription
- **anthropic** - Anthropic API client for summarization

**Performance considerations**:
- First Whisper model load is slow (downloading/loading weights)
- Transcription time scales with audio duration (roughly real-time on CPU)
- GPU acceleration available if torch detects CUDA

### Conda Packages

The file `conda_packages.txt` lists a single package:
```
ffmpeg-python
```

This suggests FFmpeg might need special handling via conda in some environments.

## Working with the Codebase

### Adding New Features

1. Check if feature aligns with design/design.md architecture
2. If yes, implement following the target structure (pipeline/, clients/, steps/)
3. If no, discuss scope and update design document first
4. Always add tests (or at minimum, manual testing steps)
5. Update CLI help text and this CLAUDE.md as needed

### Debugging Pipeline Issues

Each pipeline stage writes to stdout/stderr via logging:
- **video_extraction**: FFmpeg operations and track identification
- **audio_transcription**: Whisper model loading and transcription progress
- **transcript_merger**: Segment merging and overlap detection
- **summarize_transcript**: Token estimation and API calls

Check logs for the specific stage where failure occurs.

### Common Development Workflows

**Extract and transcribe a recording**:
```bash
uv run minutia extract-audio recording.mkv ./output/
uv run minutia transcribe ./output/microphone_audio.wav ./output/desktop_audio.wav ./output/
uv run minutia merge-transcripts ./output/microphone_transcript.txt ./output/desktop_transcript.txt ./output/merged.json
uv run minutia summarize ./output/merged.json ./output/summary.txt
```

**Full pipeline in one command**:
```bash
uv run minutia process-all recording.mkv ./output/
```

**Development iteration cycle**:
```bash
make lint-fix              # Fix linting issues
make format                # Format code
make test                  # Run tests (when implemented)
uv run minutia <command>   # Test CLI changes
```
