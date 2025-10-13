# Minutia Package Design Document

## Overview

This document outlines the design and architecture for the `minutia` Python package. The primary purpose of this package is to provide a robust, extensible, and user-friendly tool for transcribing and summarizing audio and video files. It is designed as a command-line application with a rich user interface, supporting modular components for transcription and summarization to allow for future expansion.

The core functionality revolves around two main pipelines: a full video-to-summary workflow that extracts audio from MKV files, and a direct audio-to-summary workflow. The system is built to be highly configurable, utilizing a central settings management system that can be controlled via environment variables, configuration files, and command-line arguments.

### Core Libraries and Technologies

The package will be built upon a modern Python stack, leveraging the following key libraries:

*   **CLI Framework**: `click` will be used for creating a powerful and intuitive command-line interface.
*   **Configuration**: `pydantic` and `pydantic-settings` will manage all configuration, providing data validation and flexible loading from multiple sources.
*   **User Interface**: `rich` will provide a polished terminal experience with progress bars, formatted tables, and colored output.
*   **AI Services**: `anthropic` for summarization via Claude models and `openai-whisper` for audio transcription.
*   **Media Processing**: `ffmpeg-python` will handle the audio extraction from video files.
*   **Development & Quality**: `ruff` for linting and formatting, `pytest` for testing, and `mypy` for static type checking.

### Table of Contents

1.  [Package Architecture](#package-architecture)
    1.  [Configuration Management](#configuration-management)
    2.  [Provider Architecture](#provider-architecture)
    3.  [Pipeline Orchestration](#pipeline-orchestration)
    4.  [Smart Filepath Handling](#smart-filepath-handling)
    5.  [Command-Line Interface (CLI)](#command-line-interface-cli)
    6.  [Data Modeling](#data-modeling)
2.  [Remaining Gaps](#remaining-gaps)

## Package Architecture

The package is designed with a modular and decoupled architecture to promote extensibility and maintainability. The source code is organized into distinct directories, each with a clear responsibility, from configuration and providers to processing logic and the user-facing CLI.

### Configuration Management

Configuration is centralized using `pydantic-settings` to provide a flexible and powerful system. This allows settings to be loaded from environment variables, a `.env` file, and command-line arguments, with clear precedence.

*   **`config/settings.py`**: This file will contain `pydantic.BaseSettings` models that define the entire configuration structure for the application. This includes nested settings for audio processing, transcription, summarization, and output management.
*   **`config/defaults.py`**: This module will house default values and constants, ensuring that the application can run with a sensible baseline configuration out-of-the-box.
*   **CLI Integration**: The CLI will leverage this configuration system to allow users to override any setting directly from the command line, providing maximum flexibility for a single run.

### Provider Architecture

To ensure the package is not tightly coupled to specific AI services, we will implement a pluggable provider architecture. This allows for different transcription and summarization backends to be used interchangeably.

*   **Base Classes**: Abstract base classes (`TranscriptionProvider`, `SummarizationProvider`) in `providers/base.py` will define the common interface that all providers must implement. This ensures consistent behavior and method signatures (e.g., `transcribe()`, `summarize()`).
*   **Concrete Implementations**: Specific providers, such as `WhisperProvider` and `ClaudeProvider`, will be implemented in their own modules (e.g., `providers/transcription/whisper.py`). Each will handle the unique logic of interacting with its respective API.
*   **Registry System**: A registry in `providers/.../registry.py` will allow providers to be discovered and loaded dynamically. This will make it simple to add new providers in the future without modifying the core pipeline logic. The CLI will use this registry to list available providers and their supported models.

### Pipeline Orchestration

The core logic of the application is managed by pipeline orchestrators. These classes are responsible for executing the sequence of steps required to process a file, from input to final output, while providing rich feedback to the user.

*   **`core/pipelines.py`**: This module will contain the main pipeline classes, `VideoPipeline` and `AudioPipeline`.
*   **`VideoPipeline`**: Manages the end-to-end workflow for video files: audio extraction, transcription of multiple audio tracks, merging transcripts, and generating a summary.
*   **`AudioPipeline`**: Manages a simplified workflow for pre-existing audio files, skipping the extraction step.
*   **Progress Tracking**: Both pipelines will be tightly integrated with the `rich` library to display real-time progress bars and status updates for each step of the process, enhancing the user experience.

### Smart Filepath Handling

File and directory path management will be handled by a dedicated utility to ensure predictable and intuitive behavior. This avoids scattering path manipulation logic throughout the codebase.

*   **`utils/paths.py`**: A `PathManager` class will be responsible for resolving output directories and generating filenames.
*   **Output Directory Logic**: The manager will determine the final output directory based on a clear hierarchy: a user-provided directory via the CLI takes highest precedence, followed by a configured directory in the settings, and finally defaulting to a new directory created alongside the input file (e.g., `input_file_output/`).
*   **Naming Strategy**: Filename generation will be configurable, with a default strategy of prepending a timestamp (e.g., `20251013_143000_summary.txt`) to avoid name collisions and maintain a chronological record.

### Command-Line Interface (CLI)

The CLI is the primary user entry point, built with `click`. It is designed to be both powerful for advanced users and simple for basic use cases, with clear commands, options, and help messages.

*   **`cli/main.py`**: This file defines the main `click` group and commands.
*   **Commands**: The CLI will feature distinct commands for different operations:
    *   `process-video`: Runs the full MKV-to-summary pipeline.
    *   `process-audio`: Runs the audio-to-summary pipeline.
    *   `list-providers`: Displays available transcription and summarization providers and their models.
    *   `show-config`: Prints the current application configuration, showing the final values merged from all sources.
*   **Rich UI Integration**: The CLI will use `rich` to present information in a clean, readable format, including tables for listing providers and styled panels for displaying configuration.

### Data Modeling

Data structures for inputs, outputs, and intermediate results are explicitly defined using `pydantic` models. This approach ensures data consistency, provides automatic validation, and creates a self-documenting schema for the entire application. The core models are designed to be comprehensive, capturing all relevant information from a processing job, from metadata to the final output.

The main models will be defined in `src/minutia/data/models.py`.

#### Core Data Models

The following Pydantic models define the primary data structures for the application.

```python
# src/minutia/data/models.py
from datetime import datetime
from typing import List, Dict, Optional

from pydantic import BaseModel, Field

class TranscriptSegment(BaseModel):
    """Represents a single, timestamped segment of a transcript."""
    start: float = Field(..., description="The start time of the segment in seconds.")
    end: float = Field(..., description="The end time of the segment in seconds.")
    text: str = Field(..., description="The transcribed text of the segment.")

class ProcessingMetadata(BaseModel):
    """Contains metadata about the entire processing job."""
    input_file: str = Field(..., description="The absolute path to the input file.")
    output_paths: Dict[str, str] = Field(
        default_factory=dict,
        description="A map of output types (e.g., 'summary', 'transcript_json') to their file paths."
    )
    processing_start_time: datetime = Field(..., description="The UTC timestamp when processing began.")
    processing_duration_seconds: float = Field(..., description="The total duration of the processing job in seconds.")
    transcription_provider: str = Field(..., description="The identifier for the transcription provider used.")
    transcription_model: str = Field(..., description="The specific model used for transcription.")
    summarization_provider: str = Field(..., description="The identifier for the summarization provider used.")
    summarization_model: str = Field(..., description="The specific model used for summarization.")
    estimated_cost: Optional[float] = Field(None, description="An estimated cost for the API calls made, if available.")
    package_version: str = Field(..., description="The version of the minutia package that ran the process.")

class ProcessingResult(BaseModel):
    """The final, structured output of a processing pipeline."""
    metadata: ProcessingMetadata = Field(..., description="All metadata related to the processing job.")
    summary: str = Field(..., description="The final generated summary.")
    transcript: List[TranscriptSegment] = Field(..., description="The structured transcript with timestamped segments.")
    merged_transcript_text: str = Field(..., description="A simple string representation of the full transcript.")
```

#### Serialization and Output

The `ProcessingResult` model is the top-level container for all job-related data. It is designed to be easily serialized to a JSON file, providing a comprehensive, machine-readable record of the run.

*   **`data/formats.py`**: This module will contain helper functions to handle the serialization of the `ProcessingResult` model into different file formats.
    *   `save_result_as_json(result: ProcessingResult)`: This function will use `result.model_dump_json(indent=2)` to produce a formatted JSON file.
    *   `save_summary_as_text(result: ProcessingResult)`: This will write the `result.summary` to a plain `.txt` file.
    *   `save_transcript_as_text(result: ProcessingResult)`: This will write the `result.merged_transcript_text` to a plain `.txt` file.

Example JSON Output (`..._result.json`):
```json
{
  "metadata": {
    "input_file": "/path/to/meeting.mkv",
    "output_paths": {
      "summary": "/path/to/output/20251013_143000_summary.txt",
      "transcript_json": "/path/to/output/20251013_143000_transcript.json",
      "result_json": "/path/to/output/20251013_143000_result.json"
    },
    "processing_start_time": "2025-10-13T14:30:00.123456Z",
    "processing_duration_seconds": 125.6,
    "transcription_provider": "whisper",
    "transcription_model": "whisper-3",
    "summarization_provider": "claude",
    "summarization_model": "claude-3-opus-20240229",
    "estimated_cost": 0.08,
    "package_version": "0.1.0"
  },
  "summary": "The team discussed the Q4 roadmap and decided to prioritize the new user authentication feature...",
  "transcript": [
    {
      "start": 0.5,
      "end": 4.2,
      "text": "Okay, let's kick off the meeting."
    },
    {
      "start": 4.5,
      "end": 8.9,
      "text": "First on the agenda is the Q4 roadmap planning."
    }
  ],
  "merged_transcript_text": "Okay, let's kick off the meeting.\nFirst on the agenda is the Q4 roadmap planning."
}
```

#### Integration Points

*   **Pipeline Orchestration**: The `VideoPipeline` and `AudioPipeline` in `core/pipelines.py` are responsible for instantiating and populating these models. At the end of a successful run, a pipeline will return a complete `ProcessingResult` object.
*   **CLI**: The CLI in `cli/main.py` will receive the `ProcessingResult` object from the pipeline and use the helper functions in `data/formats.py` to write the final output files to the disk based on the paths in `metadata.output_paths`.
*   **Path Management**: The `PathManager` in `utils/paths.py` will be used by the pipelines to generate the file paths that are stored in `metadata.output_paths`.

## Remaining Gaps

This section identifies areas that were not fully detailed in the initial planning phase and require further discussion and decision-making.

*   **__meta: [Custom Exception Hierarchy]__**
    We have a placeholder for `core/exceptions.py`, but the specific exception types and their hierarchy have not been designed. We need to define custom exceptions for common failure modes, such as `ProviderError`, `ConfigurationError`, or `FileProcessingError`, to enable more granular error handling and reporting in the pipelines and CLI.

*   **__meta: [Detailed Data Models]__**
    The plan mentions `data/models.py` for `ProcessingResult` and other structures, but the exact fields and relationships are not specified. We need to define the schemas for the final JSON output, the merged transcript format, and any metadata we want to persist, such as processing time, model versions, and cost estimates.

*   **__meta: [Provider Configuration Schema]__**
    The `TranscriptionSettings` and `SummarizationSettings` include a `provider_config: Dict[str, Any]` field for provider-specific settings. This is flexible but not type-safe. We should explore using discriminated unions in Pydantic to create specific configuration models for each provider (e.g., `WhisperConfig`, `ClaudeConfig`) to improve validation and developer experience.

*   **__meta: [Testing Strategy and Scope]__**
    The plan lists `pytest` and `mypy` as development tools, but we haven't defined a concrete testing strategy. We need to decide on the scope of unit tests vs. integration tests. For example, should we mock all external API calls? How will we test the `rich` UI components and the file I/O operations in `PathManager`?

*   **__meta: [Logging Configuration and Format]__**
    The settings include `log_level` and `debug` flags, but the specifics of the logging configuration are absent. We need to decide on a structured logging format (e.g., JSON), where logs should be written (console and/or file), and what information should be included in log records to facilitate effective debugging.

*   **__meta: [Handling of Large Files and Streaming]__**
    The current design implicitly assumes that audio and transcript data can be held in memory. We need to consider the implications of very large files. Should we investigate streaming data between processing steps to reduce memory consumption, especially for the transcription and summarization phases? This could impact the design of the provider interfaces.
