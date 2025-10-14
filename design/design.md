# Minutia MVP Design

## Overview

This document defines the minimum viable product for the refactored Minutia CLI. It captures the scope, responsibilities, and coordination plan required to deliver a dependable transcription and summarization workflow while keeping the implementation lean enough for a fast iteration cycle.

## MVP Scope & Goals

- **Consistent file handling**: accept either a full MKV or pre-extracted audio pair, create a dated run directory, and emit predictable filenames for all artifacts.
- **Media processing pipeline**: extract two audio tracks from MKV, run Whisper transcription, merge outputs into a structured transcript, and optionally call Anthropic for summaries.
- **CLI with progress visibility**: provide a single `minutia process` entry point (plus targeted subcommands if needed) with `rich` progress indicators and friendly status panels.
- **Prepared for future phases**: surface clear extension points without introducing registries or multi-provider abstractions yet.
- **Unified logging**: replace ad-hoc loggers with `loguru` and keep stdout free for user-facing CLI output.

Anything outside of this scope (LLM-based filename generation, personal note injection, notebook widgets, provider registries) is explicitly deferred.

### Ground Zero: Pipeline Verification

Before any refactoring, establish baseline functionality:
- **Verify CreateTranscriptProd.ipynb runs end-to-end** with current test recording
- **Create standalone script version** that replicates notebook functionality
- **Add basic integration test** to ensure pipeline doesn't break during migration
- **Document current feature set** including advanced summarization capabilities

## Architecture Summary

```
CLI (rich) ──▶ Pipeline Orchestrator ──▶
  ├─▶ Path Manager
  ├─▶ Video Extraction (ffmpeg)
  ├─▶ Audio Transcription (Whisper)
  ├─▶ Transcript Merge
  └─▶ Summary Generation (optional)
                 │
                 └─▶ Outputs (JSON transcript, TXT summary, logs)
```

Each module operates on simple data contracts so teams can work in parallel. Shared contexts and results are intentionally narrow to keep onboarding easy for junior contributors.

## Component Designs

### Migration Assessment: Current vs Target State

Based on analysis of the working CreateTranscriptProd.ipynb pipeline:

**✅ PRESERVE (Working Well, Minimal Changes):**
- **Video Extraction**: Robust FFmpeg integration with track detection and error handling
- **Audio Transcription**: Mature Whisper integration with model flexibility and GPU/CPU fallback
- **Transcript Merger**: Sophisticated overlap detection and merging logic with metadata generation
- **Summarization**: Advanced prompt engineering with personal notes integration and cost estimation
- **Core Pipeline Flow**: End-to-end processing logic is proven and production-ready

**🔄 REFACTOR (Good Logic, Interface Updates):**
- **Path Management**: Currently ad-hoc path construction, needs RunPaths standardization
- **Logging**: Multiple basic loggers across modules, needs loguru unification
- **CLI Interface**: Currently notebook-based, needs rich CLI wrapper with progress reporting
- **Configuration**: Environment variables scattered across modules, needs centralization

**🆕 NEW (Missing Infrastructure):**
- **End-to-end script**: Convert notebook workflow to standalone CLI script
- **Test suite**: Unit and integration tests for pipeline verification and regression prevention
- **Settings module**: Centralized configuration management with validation
- **Pipeline orchestrator**: Formal state management and event system for progress reporting

### Path Management (`minutia.paths`)

**Responsibilities**
- Resolve the working directory for a run using the current ISO date and optional user-provided subfolder.
- Produce canonical filenames for extracted audio, transcripts, summaries, and logs.
- Provide helper methods for locating existing artifacts when starting from audio files.

**Critical contract**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RunPaths:
    run_root: Path
    input_path: Path
    microphone_audio: Path
    desktop_audio: Path
    transcripts_dir: Path
    summary_file: Path
    metadata_file: Path
```

This dataclass is the shared currency between the CLI, pipeline, and downstream modules. Every step either consumes or enriches `RunPaths` data to avoid bespoke path juggling.

### Media Extraction (`minutia.video`)

- Wrap `ffmpeg-python` calls to extract exactly two audio tracks from MKV.
- Honor CLI-provided track indices; fail fast with clear error messages when tracks are missing.
- Output audio files using `RunPaths.microphone_audio` and `RunPaths.desktop_audio`.
- No Whisper, Transformers, or Anthropic imports in this module—keep dependencies tight.

### Audio Transcription (`minutia.transcription`)

- Load the Whisper model identified in configuration (default `base`).
- Emit structured JSON (segments, language, duration) rather than plain text to simplify merging.
- Persist transcript JSON in `RunPaths.transcripts_dir`, returning a lightweight object with file references.
- Provide CPU-friendly defaults and log model/device decisions via `loguru`.

### Transcript Merge (`minutia.transcripts`)

- Read the JSON outputs from transcription and merge segments by timestamp, retaining source labels.
- Produce a combined transcript structure plus a flattened text version for the summarizer.
- Write a merged artifact (`RunPaths.metadata_file`) containing metadata (input sources, segment count, total duration).
- Leave overlap heuristics straightforward (no advanced diarization in MVP).

### Summary Generation (`minutia.summary`)

- Optional stage triggered when `--skip-summary` is not set and `ANTHROPIC_API_KEY` is available.
- Reuse the existing prompt template with minimal adjustments; expose knobs for future prompt refinements via configuration.
- Return summary text and persist it to `RunPaths.summary_file`.
- Capture cost estimations only if trivial; otherwise record a TODO for the next phase.

### Pipeline Orchestration (`minutia.pipeline`)

**Current State**: Direct module calls in notebook cells with manual error handling
**Target State**: Formal orchestrator managing step execution, state, and reporting

**Core Responsibilities**:
- **Step Management**: Execute video extraction → transcription → merging → summarization
- **State Tracking**: Maintain pipeline state and enable resume-from-failure capability
- **Event System**: Emit structured events for progress reporting and logging correlation
- **Error Recovery**: Handle failures gracefully with clear, actionable error messages
- **Context Passing**: Thread RunPaths and configuration through all pipeline steps

**Implementation Pattern (Simple Callback-Based Events)**:
```python
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class StepProgress:
    step_name: str
    status: StepStatus
    message: str = ""
    error: Optional[Exception] = None

@dataclass
class PipelineConfig:
    input_path: Path
    whisper_model: str = "base"
    skip_summary: bool = False
    mic_track: int = 3
    desktop_track: int = 2

class PipelineOrchestrator:
    def __init__(self, progress_callback: Callable[[StepProgress], None] = None):
        self.progress_callback = progress_callback or (lambda x: None)
        self.steps = ["extract_audio", "transcribe", "merge", "summarize"]
    
    def _report_progress(self, step_name: str, status: StepStatus, message: str = ""):
        progress = StepProgress(step_name, status, message)
        self.progress_callback(progress)
        
    def execute(self, config: PipelineConfig) -> PipelineResult:
        for step_name in self.steps:
            self._report_progress(step_name, StepStatus.RUNNING, f"Starting {step_name}")
            try:
                # Execute step logic here
                self._report_progress(step_name, StepStatus.COMPLETED, f"Finished {step_name}")
            except Exception as e:
                self._report_progress(step_name, StepStatus.FAILED, str(e))
                raise
```

**Key Design Decisions**:
- Simple callback pattern instead of complex event buses
- Explicit step enumeration for predictable progress reporting
- Exception-based error handling with structured progress updates
- Stateless orchestrator that can be easily tested and debugged

### CLI Experience (`minutia.cli`)

- Provide a `minutia process` command that accepts `--input`, optional `--mic-track`/`--desktop-track`, `--skip-summary`, and `--whisper-model`.
- Use `rich` to render:
  - a progress bar that tracks the pipeline steps,
  - status panels summarizing output locations, and
  - styled error messages when exceptions bubble up.
- Keep stdout reserved for user-facing text; route logs through `loguru`.

### Configuration & Secrets

- Centralize CLI defaults and environment overrides in a small `settings` module (simple `dataclass` or `pydantic` as needed).
- Read `.env` for API keys; do not block the pipeline when the Anthropic key is absent—just skip summarization with a warning.

## Logging & Telemetry

- Initialize `loguru` at process start with a JSON-friendly sink for the run directory and a colored sink for stderr (debug-level off by default).
- Assign contextual fields (`step`, `input_file`, `run_root`) when entering each pipeline stage to simplify log correlation.
- Ensure third-party libraries’ loggers are either routed through loguru or silenced to prevent duplicate output.
- Provide guidance in the repo README for accessing logs post-run.

## Collaboration & Async Delivery

### Workstream Ownership

- **Path Management & Settings**: define `RunPaths`, directory creation rules, and configuration loader.
- **Pipeline & CLI**: implement orchestrator, integrate `rich` UI, and wire command-line interface.
- **Media & Transcription**: handle ffmpeg extraction, Whisper transcription, and transcript persistence.
- **Merge & Summary**: build transcript merger, optional summarization call, and final artifacts.
- **QA & Validation**: craft smoke tests, golden sample runs, and documentation updates.

Each workstream has minimal shared code surfaces (primarily `RunPaths` and pipeline events), allowing developers to operate independently once interfaces are agreed.

### Coordination Practices

- Maintain a canonical status board (e.g., GitHub Projects) with columns for Ready, In Progress, Blocked, Review, Done.
- Require short daily async updates in a shared channel (e.g., thread with completed/next blockers) to bridge time zones.
- Use feature branches per task, keeping pull requests under ~400 lines to ease review for junior contributors.
- Capture decisions and open questions in a `docs/notes.md` log so team members starting their day have context.
- Schedule a weekly synchronous sync with overlapping hours to unblock structural issues; otherwise rely on detailed PR descriptions and annotated TODOs.
- Encourage pairing through recorded walkthroughs when asynchronous schedules prevent live sessions—store summaries in the status board.

### Definition of Done Checklist

Every task should ship with:
- **Regression Prevention**: Unit or integration tests that prevent breaking existing functionality
- **Loguru instrumentation**: Verified locally with proper contextual fields
- **CLI help text**: Updated to reflect new options and maintain existing functionality
- **Documentation**: Edge cases, TODOs, and migration notes captured in task comments
- **Pipeline Integration**: Changes work with both standalone script and pipeline orchestrator
- **Golden Sample Validation**: New code passes tests against known-good pipeline runs

## Migration-First Task Breakdown for Junior Developers

### Phase 1: Foundation & Verification (Critical Path)
1. **Pipeline Verification & Baseline Script**
   - Verify CreateTranscriptProd.ipynb runs end-to-end with test recording
   - Convert notebook cells to standalone Python script preserving all working logic
   - Add basic integration test that runs full pipeline and validates outputs
   - Document current advanced features (personal notes, cost estimation, auto-filenames)

### Phase 2: Pipeline Architecture (Core Focus)
2. **Pipeline Orchestration Implementation**
   - Implement PipelineOrchestrator class with callback-based progress reporting
   - Create PipelineConfig dataclass for input parameters
   - Add structured exception handling and error recovery
   - Build step enumeration and state tracking
   - Add unit tests for orchestrator logic

### Phase 3: Infrastructure Migration (Parallel to Phase 2)
3. **RunPaths & Path Management**
   - Implement RunPaths dataclass with factory methods (`from_video_input`, `from_audio_inputs`)
   - Migrate existing modules to use RunPaths instead of ad-hoc path construction
   - Ensure directories created lazily with proper validation
   - Add unit tests for path resolution and directory creation

4. **Logging Infrastructure**
   - Replace multiple basic loggers with unified loguru setup
   - Add contextual fields (`step`, `input_file`, `run_root`) for log correlation
   - Configure JSON sink for run directory and colored stderr sink
   - Integrate with pipeline orchestrator for structured logging

5. **Settings & Configuration**
   - Create centralized settings module with dataclass/pydantic validation
   - Migrate scattered environment variable loading to single configuration loader
   - Add `.env` file support and API key validation
   - Provide sensible defaults matching current working behavior

### Phase 4: CLI Enhancement (Depends on Phases 2-3)
6. **Rich CLI Integration**
   - Wrap pipeline orchestrator with Click CLI interface
   - Add rich progress bars connected to pipeline progress callbacks
   - Implement styled output panels showing artifact locations
   - Map pipeline exceptions to friendly CLI error messages
   - Preserve all current CLI arguments and functionality

### Testing Strategy Throughout Migration
- **Unit Tests**: Add tests for each component as it's refactored to prevent regressions
- **Integration Tests**: Maintain end-to-end test that validates complete pipeline functionality
- **Smoke Tests**: Quick validation tests for rapid feedback during development
- **Golden Samples**: Use existing successful runs as regression test baselines

**Dependencies & Parallelization**:
- Phase 1 is sequential and blocks everything else
- Phases 2-3 can run in parallel once Phase 1 completes
- Phase 4 depends on completion of Phases 2-3
- Testing work runs continuously throughout all phases

**Key Principle**: **Preserve working functionality first, enhance second**. Never break the existing pipeline during migration.

## Future-Ready Hooks

- Leave TODO markers for provider abstraction, cost tracking, and advanced overlap handling; keep interfaces narrow so replacements can slot in later.
- Document gaps in the design doc appendices to revisit during the post-MVP planning cycle.

## Acceptance Criteria

- End-to-end run starting from MKV produces extracted audio, transcript JSONs, merged transcript, and optional summary in a timestamped directory.
- CLI progress output clearly shows each step and final artifact locations.
- Logs are routed through loguru with contextual fields and stored alongside outputs.
- Modules align with the contracts outlined above, enabling straightforward extension work for subsequent phases.
