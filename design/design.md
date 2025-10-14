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
- Handle directory naming collisions and cleanup policies.
- Normalize input paths (relative → absolute) and validate accessibility.

**Critical contract**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
from enum import Enum

class CleanupPolicy(Enum):
    KEEP_ALL = "keep_all"
    KEEP_FINAL = "keep_final"  # Remove intermediate audio files
    CLEANUP_ON_ERROR = "cleanup_on_error"

@dataclass(frozen=True)
class RunPaths:
    run_root: Path
    input_path: Path
    microphone_audio: Path
    desktop_audio: Path
    transcripts_dir: Path
    summary_file: Path
    metadata_file: Path
    logs_file: Path
    
    @classmethod
    def from_video_input(
        cls, 
        input_path: Union[str, Path], 
        base_output_dir: Optional[Path] = None,
        run_suffix: Optional[str] = None
    ) -> 'RunPaths':
        """Create RunPaths from MKV/video input.
        
        Args:
            input_path: Path to video file (relative paths resolved to absolute)
            base_output_dir: Base directory for runs (default: ./runs)
            run_suffix: Optional suffix for run directory collision handling
            
        Returns:
            RunPaths with collision-safe directory structure
            
        Example:
            /project/runs/2024-01-15_meeting-recording/
            ├── audio/
            │   ├── microphone.wav
            │   └── desktop.wav
            ├── transcripts/
            │   ├── microphone_transcript.json
            │   └── desktop_transcript.json
            ├── merged_transcript.json
            ├── summary.txt
            ├── metadata.json
            └── minutia.log
        """
        pass
    
    @classmethod
    def from_audio_inputs(
        cls,
        mic_audio_path: Union[str, Path],
        desktop_audio_path: Union[str, Path],
        base_output_dir: Optional[Path] = None
    ) -> 'RunPaths':
        """Create RunPaths when starting from pre-extracted audio files.

        Directory naming strategy:
        - Use parent directory name + timestamp for uniqueness
        - Example: If audio files are in /data/meeting_audio/,
          run directory becomes: ./runs/2024-01-15_meeting_audio/

        Args:
            mic_audio_path: Path to microphone audio file
            desktop_audio_path: Path to desktop audio file
            base_output_dir: Base directory for runs (default: ./runs)

        Returns:
            RunPaths with structure:
            /project/runs/2024-01-15_audio_parent/
            ├── audio/ (symlinks or copies of original files)
            │   ├── microphone.wav -> /original/path/mic.wav
            │   └── desktop.wav -> /original/path/desktop.wav
            ├── transcripts/
            ├── merged_transcript.json
            ├── summary.txt
            ├── metadata.json
            └── minutia.log
        """
        pass
    
    def ensure_directories(self) -> None:
        """Create all required directories with proper permissions."""
        pass
    
    def cleanup(self, policy: CleanupPolicy = CleanupPolicy.KEEP_ALL) -> None:
        """Clean up intermediate files based on policy."""
        pass

# Directory naming collision handling
def resolve_run_directory(
    base_name: str, 
    base_dir: Path, 
    max_attempts: int = 100
) -> Path:
    """
    Resolve directory name with collision handling.
    
    Strategy:
    - First attempt: {base_name}
    - Collisions: {base_name}_2, {base_name}_3, etc.
    - After max_attempts, raise error with guidance
    
    Examples:
        2024-01-15_meeting-recording/
        2024-01-15_meeting-recording_2/  (if collision)
    """
    pass
```

**Path Resolution Rules**
- **Input paths**: Always convert relative paths to absolute using `Path.resolve()`
- **Output directories**: Create under `./runs/{YYYY-MM-DD}_{input_basename}/` by default
- **Collision handling**: Append `_N` suffix when directories exist (fail after 100 attempts)
- **Permissions**: Create directories with 0755, files with 0644
- **Validation**: Verify input file exists and is readable before creating output structure

**Cleanup Strategies**
- `KEEP_ALL`: Preserve all intermediate files (default, safest for debugging)
- `KEEP_FINAL`: Remove extracted audio after successful transcription
- `CLEANUP_ON_ERROR`: Remove entire run directory if pipeline fails completely

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

### Data Formats & Schemas

**Current vs. MVP Structure:**

*Current approach* stores individual transcripts as plain text with bracketed timestamps:

```text
[0.00 - 2.00]  you
[30.00 - 32.00]  hello world
```

*MVP approach* uses consistent JSON throughout the pipeline for easier parsing while preserving current functionality.

#### Individual Transcript JSON Schema (MVP)

```json
{
  "metadata": {
    "source_file": "path/to/microphone_audio.wav",
    "model": "whisper-base",
    "language": "en", 
    "duration": 2005.0,
    "processed_at": "2025-03-18T16:46:00+00:00"
  },
  "segments": [
    {
      "start": 0.0,
      "end": 2.0,
      "text": "Hello world"
      // TODO: Add confidence scores when Whisper JSON output is implemented
      // TODO: Add segment IDs for overlap tracking (post-MVP)
      // TODO: Add no_speech_prob filtering (post-MVP)
    }
  ]
}
```

#### Merged Transcript Schema (Current + Minimal Changes)

```json
{
  "metadata": {
    "source_files": {
      "microphone": "transcripts/microphone_transcript.json", // MVP: change .txt to .json
      "desktop": "transcripts/desktop_transcript.json"
    },
    "total_duration": 2005.0,
    "segment_count": 215,
    "parse_overlaps": false  // MVP: keep current behavior
    // TODO: Add run_id, merge_strategy, overlap_detection (post-MVP)
    // TODO: Add created_at timestamp (post-MVP)
  },
  "transcript": [
    {
      "source": "microphone",
      "start_time": 0.0,
      "end_time": 2.0,
      "text": "Hello everyone"
      // TODO: Add unique segment IDs (post-MVP) 
      // TODO: Add confidence scores (post-MVP)
      // TODO: Add speaker_id support (post-MVP)
      // TODO: Add overlap_with references (post-MVP)
    }
  ]
}
```

#### Run Metadata Schema (MVP - NEW but minimal)

```json
{
  "run_info": {
    "started_at": "2025-03-18T16:40:00+00:00",
    "completed_at": "2025-03-18T16:46:32+00:00", 
    "status": "completed"
    // TODO: Add run_id generation (post-MVP)
    // TODO: Add pipeline_version tracking (post-MVP)
  },
  "input": {
    "source_file": "/path/to/meeting.mkv",
    "duration": 2005.0
    // TODO: Add file_size, sample_rate details (post-MVP)
    // TODO: Add track metadata (post-MVP)
  },
  "outputs": {
    "merged_transcript": "merged_transcript.json",
    "summary": "summary.txt",
    "logs": "minutia.log"
  }
  // TODO: Add processing times tracking (post-MVP)
  // TODO: Add cost tracking for API usage (post-MVP)
}
```

**MVP Scope Changes:**
1. **Convert text transcripts to JSON** - minimal change, easier parsing
2. **Add basic run metadata file** - just essential tracking
3. **Preserve all current functionality** - no feature expansion

**Deferred to Post-MVP:**
- Confidence scores and advanced Whisper metadata
- Sophisticated overlap detection and segment IDs  
- Performance timing and cost tracking
- Enhanced run identification and versioning

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
    run_paths: RunPaths  # Added: explicit RunPaths reference for all pipeline steps
    run_id: str  # Added: unique identifier for this pipeline run (ISO timestamp + hash)
    whisper_model: str = "base"
    skip_summary: bool = False
    mic_track: int = 3
    desktop_track: int = 2
    base_output_dir: Path = Path("./runs")  # Added: for RunPaths creation

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

#### Pipeline State Management & Resume Capability

**PipelineResult Definition**
```python
@dataclass
class PipelineResult:
    success: bool
    run_paths: RunPaths
    completed_steps: List[str]
    failed_step: Optional[str] = None
    error: Optional[Exception] = None
    artifacts: Dict[str, Path] = field(default_factory=dict)
    duration_seconds: float = 0.0
    
    @property
    def is_partial(self) -> bool:
        """True if some steps completed but pipeline failed overall."""
        return len(self.completed_steps) > 0 and not self.success
```

**Persistence Strategy for Resume-From-Failure**
```python
@dataclass
class PipelineState:
    run_id: str
    started_at: str  # ISO 8601 timestamp string for JSON serialization
    current_step: str
    completed_steps: List[str]
    run_paths_dict: Dict[str, str]  # RunPaths serialized as string paths
    config_dict: Dict[str, Any]  # PipelineConfig serialized as dict

    @classmethod
    def from_pipeline(cls, run_id: str, current_step: str, completed_steps: List[str],
                     run_paths: RunPaths, config: PipelineConfig) -> 'PipelineState':
        """Create PipelineState from pipeline objects with proper serialization."""
        return cls(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
            current_step=current_step,
            completed_steps=completed_steps,
            run_paths_dict={k: str(v) for k, v in asdict(run_paths).items()},
            config_dict={
                'input_path': str(config.input_path),
                'whisper_model': config.whisper_model,
                'skip_summary': config.skip_summary,
                'mic_track': config.mic_track,
                'desktop_track': config.desktop_track,
                'base_output_dir': str(config.base_output_dir)
            }
        )

    def to_run_paths(self) -> RunPaths:
        """Deserialize RunPaths from stored string paths."""
        return RunPaths(**{k: Path(v) for k, v in self.run_paths_dict.items()})

    def to_config(self, run_paths: RunPaths) -> PipelineConfig:
        """Deserialize PipelineConfig from stored dict."""
        return PipelineConfig(
            input_path=Path(self.config_dict['input_path']),
            run_paths=run_paths,
            run_id=self.run_id,
            whisper_model=self.config_dict['whisper_model'],
            skip_summary=self.config_dict['skip_summary'],
            mic_track=self.config_dict['mic_track'],
            desktop_track=self.config_dict['desktop_track'],
            base_output_dir=Path(self.config_dict['base_output_dir'])
        )

class PipelineOrchestrator:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback or (lambda x: None)
        self.steps = ["extract_audio", "transcribe", "merge", "summarize"]

    def _get_state_file_path(self, run_paths: RunPaths) -> Path:
        """State file stored in run directory to avoid concurrent run conflicts."""
        return run_paths.run_root / ".minutia_state.json"

    def save_state(self, state: PipelineState, run_paths: RunPaths):
        """Persist current pipeline state to JSON file in run directory."""
        state_file = self._get_state_file_path(run_paths)
        with open(state_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)

    def load_state(self, run_paths: RunPaths) -> Optional[PipelineState]:
        """Load previous pipeline state if exists in run directory."""
        state_file = self._get_state_file_path(run_paths)
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
                return PipelineState(**data)
        return None

    def resume_from_failure(self, run_paths: RunPaths) -> PipelineResult:
        """Resume pipeline from last completed step.

        Idempotency: Steps check for existing artifacts and skip if present.
        - extract_audio: Skip if audio files already exist with valid duration
        - transcribe: Skip if transcript JSON files exist with valid structure
        - merge: Skip if merged transcript exists with valid metadata
        - summarize: Skip if summary file exists and is non-empty
        """
        state = self.load_state(run_paths)
        if not state:
            raise ValueError("No previous state found to resume from")

        restored_config = state.to_config(run_paths)
        remaining_steps = [s for s in self.steps if s not in state.completed_steps]
        return self._execute_steps(remaining_steps, restored_config)
```

**Progress Surfacing to CLI**
```python
def create_rich_progress_callback() -> Callable[[StepProgress], None]:
    """Create callback that updates rich console display."""
    console = Console()
    progress_displays = {}
    
    def update_display(step_progress: StepProgress):
        step_name = step_progress.step_name
        
        if step_progress.status == StepStatus.RUNNING:
            console.print(f"[bold blue][{step_name}][/] {step_progress.message}")
        elif step_progress.status == StepStatus.COMPLETED:
            console.print(f"[bold green]✅ [{step_name}][/] {step_progress.message}")
        elif step_progress.status == StepStatus.FAILED:
            console.print(f"[bold red]❌ [{step_name}][/] {step_progress.message}")
    
    return update_display

# CLI Integration:
orchestrator = PipelineOrchestrator(progress_callback=create_rich_progress_callback())
result = orchestrator.execute(config)
```

**Graceful Partial Completion Handling**
```python
def execute(self, config: PipelineConfig) -> PipelineResult:
    """Execute pipeline with graceful degradation on partial failures."""
    completed_steps = []
    artifacts = {}
    start_time = time.time()

    for step_name in self.steps:
        self._report_progress(step_name, StepStatus.RUNNING, f"Starting {step_name}")

        # Save state before each step for resume capability
        state = PipelineState.from_pipeline(
            run_id=config.run_id,
            current_step=step_name,
            completed_steps=completed_steps,
            run_paths=config.run_paths,
            config=config
        )
        self.save_state(state, config.run_paths)

        try:
            step_outputs = self._execute_step(step_name, config)
            completed_steps.append(step_name)
            artifacts.update(step_outputs)
            self._report_progress(step_name, StepStatus.COMPLETED, f"Finished {step_name}")

        except Exception as e:
            self._report_progress(step_name, StepStatus.FAILED, str(e))

            # Return partial results - user gets value from completed steps
            return PipelineResult(
                success=False,
                run_paths=config.run_paths,
                completed_steps=completed_steps,
                failed_step=step_name,
                error=e,
                artifacts=artifacts,
                duration_seconds=time.time() - start_time
            )

    # All steps completed successfully - cleanup state file
    state_file = self._get_state_file_path(config.run_paths)
    if state_file.exists():
        state_file.unlink()

    return PipelineResult(
        success=True,
        run_paths=config.run_paths,
        completed_steps=completed_steps,
        artifacts=artifacts,
        duration_seconds=time.time() - start_time
    )
```

**Enhanced Design Decisions:**
- **State file in run directory** - Stored in `run_root/.minutia_state.json` to prevent concurrent run conflicts
- **Explicit serialization helpers** - `PipelineState.from_pipeline()` and `to_config()` methods handle Path → JSON conversion clearly
- **Idempotency built-in** - Each step checks for existing valid artifacts before rerunning
- **Graceful degradation** - Partial runs provide value (transcripts even if summary fails)
- **Direct callback chain** - Straightforward progress reporting to rich CLI display
- **Minimal error handling** - Clear failure points with actionable error messages

### CLI Experience (`minutia.cli`)

- Provide a `minutia process` command that accepts `--input`, optional `--mic-track`/`--desktop-track`, `--skip-summary`, and `--whisper-model`.
- Use `rich` to render:
  - a progress bar that tracks the pipeline steps,
  - status panels summarizing output locations, and
  - styled error messages when exceptions bubble up.
- Keep stdout reserved for user-facing text; route logs through `loguru`.

#### CLI Behavior & UX Flows

**Command Structure**
Single command with auto-detection - distinguishes input type by file count and extensions:

```bash
# Auto-detects MKV/MP4 video input
minutia process meeting.mkv

# Auto-detects dual audio input  
minutia process microphone.wav desktop.wav

# With custom output location
minutia process meeting.mkv --output ./custom-run/
```

**Flag Structure & Defaults**

```bash
minutia process meeting.mkv \
  --whisper-model base      # Override default model
  --mic-track 3            # Override default mic track  
  --system-track 2         # Override default system audio track
  --config .config (-c)    # Override default config location
  --no-summary            # Skip summary (default: generate summary)
  --output ./runs/ (-o)   # Override output directory
  --cleanup               # Clean intermediate files (default: keep all)
```

**Progress Display**

```text
┌── Minutia Transcription Pipeline ──┐
│ Input: meeting.mkv (1.2GB, 33:25)  │
└─────────────────────────────────────┘

[1/4] 🎬 Extracting Audio Tracks...
  ├─ Track 3 (microphone) → audio/microphone.wav ✓
  └─ Track 2 (system) → audio/system.wav ✓
  
[2/4] 🎙️ Transcribing Audio [████████░░] 80%
  ├─ Microphone (whisper-base): 156/195 segments
  └─ System (whisper-base): Processing...
  
[3/4] 📄 Merging Transcripts...
  ├─ Combined 342 segments chronologically ✓
  └─ Found 23 overlapping sections ✓
  
[4/4] 🤖 Generating Summary...
  └─ Anthropic Claude (15.2k tokens) ✓

✅ Pipeline Complete (3m 42s)
📁 Outputs: /project/runs/2024-01-15_meeting/
```

**Error Handling**

```bash
$ minutia process missing.mkv
┌─ Pipeline Error ─┐
│ Stage: Input     │
│ Code: FILE_404   │
│ Path: missing.mkv│
└──────────────────┘
Recommendation: Verify file exists and is readable

$ minutia process corrupted.mkv --mic-track 5
┌─ Pipeline Error ─────────┐
│ Stage: Audio Extraction  │
│ Code: TRACK_NOT_FOUND    │
│ Requested: Track 5       │
│ Available: [0, 1, 2]     │
└──────────────────────────┘
Recommendation: Use --mic-track with valid index (0-2)
```

**Help Text**

```bash
$ minutia process --help

minutia process - Transcribe and summarize meeting recordings

USAGE:
    minutia process <INPUT> [OPTIONS]

INPUTS:
    <VIDEO_FILE>                    Process MKV/MP4 video file
    <MIC_AUDIO> <SYSTEM_AUDIO>     Process pre-extracted audio pair

OPTIONS:
    --whisper-model <MODEL>         Whisper model [default: base]
    --mic-track <INDEX>             Microphone track index [default: 3]  
    --system-track <INDEX>          System track index [default: 2]
    --no-summary                    Skip AI summarization [default: generate]
    --output <DIR> (-o)             Output directory [default: ./runs]
    --config <FILE> (-c)            Config file [default: ./.minutia.toml]
    --cleanup                       Remove intermediate files [default: keep]
    
EXAMPLES:
    minutia process meeting.mkv
    minutia process mic.wav system.wav --whisper-model small
    minutia process recording.mkv --no-summary --output /tmp/
```

### Configuration & Secrets

**Configuration Strategy (Keep It Simple)**

**Precedence Order (Standard Pattern)**

```text
CLI flags > Environment variables > Config file > Hard-coded defaults
```

**Configuration Sources**
```python
@dataclass
class MinutiaConfig:
    # Core settings
    whisper_model: str = "base"
    output_dir: Path = Path("./runs")
    mic_track: int = 3
    system_track: int = 2
    
    # API settings
    anthropic_api_key: Optional[str] = None
    generate_summary: bool = True  # Default to true, opt-out with --no-summary
    
    # Advanced (MVP can ignore these)
    cleanup_policy: str = "keep_all"
    log_level: str = "INFO"

def load_config() -> MinutiaConfig:
    """Load configuration with proper precedence."""
    # 1. Start with defaults
    config = MinutiaConfig()
    
    # 2. Override with config file (if exists)
    config_file = find_config_file()
    if config_file:
        config = merge_config_file(config, config_file)
    
    # 3. Override with environment variables
    config = merge_env_vars(config)
    
    # 4. CLI flags override everything (handled by click)
    return config
```

**Environment Variables (Simple Naming)**
```bash
# Predictable MINUTIA_ prefix
export MINUTIA_WHISPER_MODEL=small
export MINUTIA_OUTPUT_DIR=/tmp/transcripts
export MINUTIA_MIC_TRACK=0
export MINUTIA_SYSTEM_TRACK=1

# Secrets (standard naming)
export ANTHROPIC_API_KEY=sk-ant-...

# Optional advanced settings
export MINUTIA_LOG_LEVEL=DEBUG
export MINUTIA_CLEANUP_POLICY=keep_final
```

**Config File Format (.env - Simplest)**
```bash
# .minutia or .env file (same format)
MINUTIA_WHISPER_MODEL=small
MINUTIA_OUTPUT_DIR=./my-runs
MINUTIA_MIC_TRACK=0
MINUTIA_SYSTEM_TRACK=1

# API keys can go here too (but env vars preferred)
ANTHROPIC_API_KEY=sk-ant-...
```

**Secrets Handling (Pragmatic)**
```python
def load_api_key() -> Optional[str]:
    """Load API key with fallback chain."""
    # 1. Environment variable (preferred)
    if key := os.getenv("ANTHROPIC_API_KEY"):
        return key
    
    # 2. Config file (backup)
    if config_file_exists() and (key := read_key_from_config()):
        return key
    
    # 3. No key found - warn but don't fail
    logger.warning("No Anthropic API key found. Summary generation will be skipped.")
    return None

def validate_config(config: MinutiaConfig) -> MinutiaConfig:
    """Basic validation - fail fast on critical errors."""
    # Validate output directory is writable (create if needed)
    # Note: We validate the parent exists but create the actual run directory later
    output_parent = config.output_dir.resolve()
    if output_parent.exists() and not os.access(output_parent, os.W_OK):
        raise ConfigError(f"Output directory is not writable: {output_parent}")

    # If output_dir doesn't exist, validate we can create it
    if not output_parent.exists():
        try:
            output_parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(f"Cannot create output directory: {e}")

    # Validate track numbers are reasonable
    if config.mic_track < 0 or config.system_track < 0:
        raise ConfigError("Track numbers must be non-negative")

    return config
```

**Config File Discovery (Simple)**
```python
def find_config_file(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Find config file with standard search order."""
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        raise ConfigError(f"Explicit config file not found: {explicit_path}")
    
    # Standard search locations
    search_paths = [
        Path(".minutia"),      # Project-specific
        Path(".env"),          # Standard env file
        Path.home() / ".minutia",  # User global
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None  # No config file found (OK)
```

**Key Pragmatic Decisions:**

- **Simple .env file format** - Everyone knows it, no parsing complexity
- **Standard precedence** - CLI > env vars > config file > defaults
- **Predictable env var names** - `MINUTIA_` prefix for all settings
- **Graceful API key handling** - Warn and skip summary if missing
- **Basic validation** - Catch obvious errors, don't over-validate

## Logging & Telemetry

- Initialize `loguru` at process start with a JSON-friendly sink for the run directory and a colored sink for stderr (debug-level off by default).
- Assign contextual fields (`step`, `input_file`, `run_root`) when entering each pipeline stage to simplify log correlation.
- Ensure third-party libraries’ loggers are either routed through loguru or silenced to prevent duplicate output.
- Provide guidance in the repo README for accessing logs post-run.

## Repository Layout & Package Structure

**Repository Structure (UV Project)**

```
minutia/
├── pyproject.toml          # UV project config
├── uv.lock                 # UV lock file
├── README.md
├── .gitignore
├── .minutia                # Default config file
├── .github/workflows/      # CI/CD
├── src/minutia/
│   ├── __init__.py
│   ├── cli.py              # Click commands + main CLI entry point
│   ├── config.py           # Configuration loading + precedence + file discovery
│   ├── models.py           # Data models (RunPaths, PipelineResult, PipelineState, etc.)
│   ├── validation.py       # Input validation + schema validation  
│   ├── logging.py          # Loguru setup + contextual fields + sinks
│   ├── pipeline/           # Pipeline orchestration components
│   │   ├── __init__.py
│   │   ├── orchestrator.py # Main pipeline logic & coordination
│   │   ├── state.py        # State persistence & resume-from-failure
│   │   └── display.py      # Rich progress callbacks & formatting
│   ├── clients/            # AI model client wrappers
│   │   ├── __init__.py
│   │   ├── whisper_client.py    # Whisper model wrapper
│   │   └── anthropic_client.py  # Anthropic API wrapper
│   └── steps/              # Pipeline steps (domain + action naming)
│       ├── __init__.py
│       ├── video_extraction.py     # Video → audio extraction  
│       ├── audio_transcription.py  # Audio → text transcription (uses whisper_client)
│       ├── transcript_merging.py   # Multiple transcripts → merged
│       └── summary_generation.py   # Transcript → summary (uses anthropic_client)
├── tests/
│   ├── conftest.py         # Global fixtures
│   ├── unit/               # Fast tests by module
│   │   ├── test_cli.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_validation.py
│   │   ├── test_logging.py
│   │   ├── pipeline/
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_state.py
│   │   │   └── test_display.py
│   │   ├── clients/
│   │   │   ├── test_whisper_client.py
│   │   │   └── test_anthropic_client.py
│   │   └── steps/
│   │       ├── test_video_extraction.py
│   │       ├── test_audio_transcription.py
│   │       ├── test_transcript_merging.py
│   │       └── test_summary_generation.py
│   ├── integration/        # Medium tests
│   │   ├── test_whisper_integration.py
│   │   └── test_pipeline_flow.py
│   ├── slow/               # Full tests
│   │   └── test_end_to_end.py
│   └── fixtures/           # Test data
│       ├── audio/
│       ├── video/
│       └── transcripts/
├── docs/
│   ├── design.md
│   └── api.md
└── scripts/
    ├── dev_setup.sh
    └── lint.sh
```

**Module Responsibilities**

**Core Modules:**
- **`cli.py`** - Click commands, argument parsing, main entry point
- **`config.py`** - Configuration loading with precedence, file discovery, validation
- **`models.py`** - Data structures (RunPaths, PipelineResult, PipelineState, etc.)
- **`validation.py`** - Input validation, schema validation, security checks
- **`logging.py`** - Loguru setup, contextual fields, sink configuration

**`pipeline/` Package:**
- **`orchestrator.py`** - PipelineOrchestrator class, step coordination, error handling
- **`state.py`** - State persistence, JSON serialization, resume-from-failure logic
- **`display.py`** - Rich progress callbacks, progress formatting, UI components

**`clients/` Package (Future-Ready):**
- **`whisper_client.py`** - Whisper model wrapper with abstraction hooks
- **`anthropic_client.py`** - Anthropic API wrapper with provider abstraction prep

**`steps/` Package:**
- **`video_extraction.py`** - Video → audio extraction using FFmpeg
- **`audio_transcription.py`** - Audio → text transcription (uses whisper_client)
- **`transcript_merging.py`** - Multiple transcripts → merged transcript
- **`summary_generation.py`** - Transcript → summary (uses anthropic_client)

**Existing Module Mapping:**
- `src/minutia/cli.py` ← Current CLI interface
- `src/minutia/steps/video_extraction.py` ← Current `video_extraction.py` (moved)
- `src/minutia/steps/audio_transcription.py` ← Whisper integration from notebook
- `src/minutia/steps/transcript_merging.py` ← Transcript merging logic from notebook  
- `src/minutia/steps/summary_generation.py` ← Anthropic integration from notebook
- `src/minutia/pipeline/orchestrator.py` ← New pipeline orchestration logic from design
- `src/minutia/clients/*` ← New AI model wrappers for future extensibility

**Benefits:**
- **Simple navigation** - Clear module purposes, minimal nesting
- **Future-ready** - Client wrappers enable provider abstraction later
- **Test organization** - Mirrors source structure for easy test location
- **Agent-friendly** - Predictable structure for AI agents and junior developers

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

### Enhanced Testing Strategy with Mocking & Resource Management

**Architecture: Hybrid Approach with Test Categories**

#### API Mocking Strategy

**Anthropic API Mocking**
```python
@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response for summary generation."""
    return {
        "content": [{"text": "## Meeting Summary\n\nThis was a test meeting..."}],
        "usage": {"input_tokens": 1500, "output_tokens": 300}
    }

@pytest.fixture
def mock_anthropic(monkeypatch, mock_anthropic_response):
    """Mock Anthropic API calls for fast testing."""
    def mock_create(*args, **kwargs):
        return type('MockResponse', (), mock_anthropic_response)()
    
    monkeypatch.setattr('anthropic.Anthropic.messages.create', mock_create)
    return mock_anthropic_response
```

#### Whisper Resource Management

**Session-Scoped Model Loading**
```python
@pytest.fixture(scope="session")
def whisper_tiny_model():
    """Load tiny Whisper model once per test session."""
    import whisper
    model = whisper.load_model("tiny")
    yield model
    del model  # Explicit cleanup

@pytest.fixture
def mock_whisper_model(monkeypatch):
    """Mock whisper for unit tests."""
    mock_segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello world"},
        {"start": 2.0, "end": 4.0, "text": "This is a test"}
    ]
    
    def mock_transcribe(audio):
        return type('Result', (), {
            'segments': mock_segments,
            'language': 'en'
        })()
    
    mock_model = type('MockModel', (), {'transcribe': mock_transcribe})()
    monkeypatch.setattr('whisper.load_model', lambda x: mock_model)
    return mock_model
```

#### Fixture Architecture

**Layered Test Resource Management**
```python
# Session-scope expensive resources
@pytest.fixture(scope="session")
def test_audio_files(tmp_path_factory):
    """Generate test audio files once per session."""
    audio_dir = tmp_path_factory.mktemp("audio")
    return create_test_audio_files(audio_dir)

# Module-scope shared data
@pytest.fixture(scope="module") 
def sample_transcripts():
    """Load sample transcript data for module tests."""
    return load_sample_data("transcripts")

# Function-scope test isolation
@pytest.fixture
def isolated_run_dir(tmp_path):
    """Create isolated run directory for each test."""
    return create_run_paths(tmp_path)
```

#### Test Categories & Performance

**Test Markers Configuration**
```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests (fast, < 1s each)
    integration: Integration tests (medium, < 30s)  
    slow: Slow tests (full pipeline, manual runs)
    
addopts = -n auto --tb=short -v
```

#### Concrete Test Examples by Category

**Unit Tests (Fast, Mocked - < 1s each)**

```python
@pytest.mark.unit
def test_run_paths_creation(tmp_path):
    """Test RunPaths directory structure creation."""
    paths = RunPaths.from_video_input("meeting.mkv", base_output_dir=tmp_path)
    assert paths.run_root.exists()
    assert paths.transcripts_dir.exists()
    assert paths.logs_file.parent.exists()

@pytest.mark.unit
def test_pipeline_state_persistence(tmp_path, mock_whisper_model, mock_anthropic):
    """Test pipeline state save/load functionality."""
    orchestrator = PipelineOrchestrator(state_file=tmp_path / "state.json")
    config = PipelineConfig(input_path="test.mkv")
    
    state = PipelineState(run_id="test", completed_steps=["extract_audio"])
    orchestrator.save_state(state)
    
    loaded_state = orchestrator.load_state()
    assert loaded_state.run_id == "test"
    assert "extract_audio" in loaded_state.completed_steps

@pytest.mark.unit
def test_cli_input_detection():
    """Test auto-detection of video vs audio inputs."""
    assert detect_input_type(["meeting.mkv"]) == InputType.VIDEO
    assert detect_input_type(["mic.wav", "desk.wav"]) == InputType.AUDIO

@pytest.mark.unit
def test_transcript_json_schema(sample_transcripts):
    """Test transcript JSON conforms to expected schema."""
    transcript = sample_transcripts["merged_transcript.json"]
    assert "metadata" in transcript
    assert "transcript" in transcript
    assert isinstance(transcript["transcript"], list)
```

**Integration Tests (Medium, Real Models - < 30s)**

```python
@pytest.mark.integration
def test_whisper_transcription_accuracy(whisper_tiny_model, test_audio_files):
    """Test actual Whisper transcription with tiny model."""
    audio_file = test_audio_files["clear_speech.wav"]
    result = transcribe_audio(audio_file, whisper_tiny_model)
    
    assert len(result.segments) > 0
    assert result.language == "en"
    assert any("hello" in seg["text"].lower() for seg in result.segments)

@pytest.mark.integration
def test_audio_extraction_pipeline(tmp_path):
    """Test video → audio extraction with ffmpeg."""
    video_file = create_test_video_with_tracks(tmp_path)
    paths = RunPaths.from_video_input(video_file, base_output_dir=tmp_path)
    
    extract_audio_tracks(video_file, paths, mic_track=0, desk_track=1)
    
    assert paths.microphone_audio.exists()
    assert paths.desktop_audio.exists()
    assert get_audio_duration(paths.microphone_audio) > 0

@pytest.mark.integration  
def test_pipeline_resume_capability(whisper_tiny_model, mock_anthropic, tmp_path):
    """Test pipeline can resume from partial completion."""
    config = PipelineConfig(input_path="test.mkv")
    orchestrator = PipelineOrchestrator(state_file=tmp_path / "state.json")
    
    save_partial_state(["extract_audio", "transcribe"], tmp_path)
    
    result = orchestrator.resume_from_failure()
    assert result.success
    assert "transcribe" in result.completed_steps
```

**Slow Tests (Full Pipeline - Manual/Nightly)**

```python
@pytest.mark.slow
def test_full_mkv_to_summary_pipeline(tmp_path):
    """Complete pipeline test: MKV → transcripts → summary."""
    video_file = "tests/fixtures/sample_meeting.mkv"
    
    result = run_complete_pipeline(
        input_file=video_file,
        output_dir=tmp_path,
        whisper_model="base",
        skip_summary=False
    )
    
    assert result.success
    assert (tmp_path / "merged_transcript.json").exists()
    assert (tmp_path / "summary.txt").exists()
    
    transcript = load_transcript(tmp_path / "merged_transcript.json")
    assert len(transcript["transcript"]) > 10
    
    summary = (tmp_path / "summary.txt").read_text()
    assert len(summary) > 100

@pytest.mark.slow
def test_golden_sample_regression():
    """Ensure pipeline output matches known-good results."""
    # Compare current output against blessed golden samples
    pass
```

#### CI/Development Workflow

**Test Execution Strategy**
```bash
# Development: Fast feedback
pytest -m unit                    # < 10s total

# Pre-commit: Medium confidence  
pytest -m "unit or integration"   # < 2m total

# Nightly/Release: Full validation
pytest -m "unit or integration or slow"  # < 30m total
```

**Key Benefits:**
- **Fast development feedback** - Unit tests provide immediate validation
- **Realistic integration confidence** - Real models catch actual issues  
- **Comprehensive validation** - Slow tests ensure end-to-end quality
- **Manageable CI costs** - Only expensive tests run when needed
- **Clear guidance for contributors** - Concrete examples show testing patterns

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
