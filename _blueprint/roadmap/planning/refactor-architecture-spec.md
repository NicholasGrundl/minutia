# Refactor Architecture Specification: Minutia v0.2.0

## Overview
This document defines the target architecture for the Minutia refactor. It serves as the definitive reference for file structure, class interfaces, and data flows. All code changes must align with this specification.

## 1. Directory Structure (Target State)

```text
minutia/
├── pyproject.toml              # Entry point: minutia = "minutia.cli:cli"
├── .minutia/                   # User configuration directory
│   ├── SOUL.md                 # Persona/Context override (optional)
│   ├── HEARTBEAT.md            # Formatting/Rules override (optional)
│   └── NOTES.json              # Personal notes list (optional)
├── src/minutia/
│   ├── __init__.py             # Exports cli
│   ├── cli.py                  # Click CLI wrapper
│   ├── config.py               # Pydantic settings & loading logic
│   ├── logging.py              # Loguru configuration
│   ├── paths.py                # RunPaths dataclass (Artifact management)
│   ├── legacy/                 # ISOLATED Legacy Code
│   │   ├── ui_jupyter.py       # Old notebook UI
│   │   ├── claude_audio_widget.py
│   │   └── gpt_audio_widget.py
│   ├── pipeline/               # Orchestration Logic
│   │   ├── __init__.py
│   │   └── orchestrator.py     # PipelineOrchestrator class
│   └── steps/                  # Pure Functional Steps
│       ├── __init__.py
│       ├── video_extraction.py # ffmpeg-python wrapper
│       ├── audio_transcription.py # Whisper wrapper
│       ├── transcript_merger.py # JSON merging logic
│       └── summarize_transcript.py # Anthropic wrapper + Markdown gen
└── tests/
    ├── conftest.py             # Global fixtures
    ├── fixtures/               # SOURCE OF TRUTH
    │   └── scenarios/          # Real input/output sets
    ├── unit/                   # Fast logic tests (<1s)
    ├── integration/            # Step validation against fixtures (<30s)
    └── slow/                   # End-to-end regression tests (>30s)
```

## 2. Core Data Models

### `RunPaths` (in `src/minutia/paths.py`)
Centralizes all file paths. Must be immutable (frozen dataclass).
*   `run_root`: `Path`
*   `input_path`: `Path`
*   `audio_dir`: `Path`
*   `transcripts_dir`: `Path`
*   `microphone_audio`: `Path` (.wav)
*   `desktop_audio`: `Path` (.wav)
*   `merged_transcript`: `Path` (.json)
*   `summary_file`: `Path` (.txt)
*   `markdown_report`: `Path` (.md) **[NEW]**
*   `metadata_file`: `Path` (.json)
*   `logs_file`: `Path` (.log)

### `PipelineConfig` (in `src/minutia/pipeline/orchestrator.py`)
Configuration for a single run.
*   `input_path`: `Path`
*   `run_paths`: `RunPaths`
*   `whisper_model`: `str`
*   `skip_summary`: `bool`
*   `summary_model`: `str`
*   `long_summary`: `bool` **[NEW]** (Enable token continuation flow)
*   `generate_markdown`: `bool` **[NEW]** (Enable MD report)
*   `personal_notes`: `List[str]` **[NEW]** (Injected into prompt)
*   `soul_override`: `Optional[str]` **[NEW]** (Content of SOUL.md)
*   `heartbeat_override`: `Optional[str]` **[NEW]** (Content of HEARTBEAT.md)

## 3. Component Specifications

### `src/minutia/steps/summarize_transcript.py`
**Responsibilities:**
1.  **Short Summary**: Single-shot summarization (legacy logic).
2.  **Long Summary**: Token-aware continuation loop (ported from `baseline_pipeline.py`).
3.  **Filename Generation**: AI-driven filename generation for Markdown reports.
4.  **Prompt Construction**: Inject `SOUL`, `HEARTBEAT`, and `NOTES` into the system prompt.

**Key Function Signatures:**
```python
def generate_long_summary(
    transcript_text: str,
    model_name: str,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """Handles [CONTINUE] tokens for long contexts."""
    pass

def get_filename_from_content(content: str, model_name: str) -> str:
    """Generates a filesystem-safe filename based on content."""
    pass

def create_markdown_report(content: str, output_dir: Path, model_name: str) -> Path:
    """Writes content to a .md file with an AI-generated name."""
    pass
```

### `src/minutia/pipeline/orchestrator.py`
**Responsibilities:**
1.  Execute steps in order: Extract -> Transcribe -> Merge -> Summarize -> Report.
2.  Handle configuration flags (`skip_summary`, `generate_markdown`).
3.  Report progress via callbacks.
4.  Save metadata (`ProcessingResult`).

**New Step:**
*   `generate_report`: Optional step. Runs only if `config.generate_markdown` is True. Calls `summarize_transcript.create_markdown_report`.

## 4. Configuration Loading (`src/minutia/config.py`)
**Responsibilities:**
1.  Load env vars and CLI args (Pydantic).
2.  **[NEW]** Scan `.minutia/` directory for `SOUL.md`, `HEARTBEAT.md`, `NOTES.json`.
3.  Inject content into `PipelineConfig`.
