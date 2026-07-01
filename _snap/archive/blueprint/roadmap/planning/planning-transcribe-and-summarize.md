# Minutia Refactor Design Document: Modern Package Architecture

## MVP Scope Definition

### Core Goals
Build a clean, extensible package focused on transcription and summarization with:

1. **Rich CLI Experience** - Progress bars, colored output, clear status updates
2. **Dual Pipeline Support** - MKV-to-summary and audio-to-summary workflows  
3. **Configuration Management** - YAML-based config with sensible defaults
4. **Provider Architecture** - Pluggable transcription and summarization backends
5. **Smart Filepath Handling** - Intuitive input/output path management

### Current State Analysis

#### Example Notebook Flow (CreateTranscriptProd.ipynb)
The notebook demonstrates the complete workflow:

1. **Setup & Configuration** - Environment variables, output directories, parameters
2. **Video Processing** - Extract audio from MKV files using `video_extraction.process_mkv_file()`
3. **Audio Transcription** - Process both microphone and desktop audio using `audio_transcription.process_audio_files()`
4. **Transcript Merging** - Combine transcripts with `transcript_merger.process_transcripts()`
5. **Summarization** - Generate AI summaries using `summarize_transcript` functions
6. **Output Management** - Save results with auto-generated filenames

### Current Source Code Architecture

#### Key Modules and Classes:

**1. `cli.py` (src/minutia/cli.py:1-131)**
- **Primary Interface**: Click-based CLI with commands: `extract-audio`, `transcribe`, `merge-transcripts`, `summarize`, `process-all`
- **Orchestration**: `process_all()` runs complete pipeline from video � summary
- **Error Handling**: Comprehensive logging and exception handling throughout

**2. `video_extraction.py` (src/minutia/video_extraction.py:1-156)**
- **Core Function**: `process_mkv_file()` - extracts audio tracks from MKV files
- **Audio Track Management**: Identifies mic vs desktop audio based on track numbers
- **Dependencies**: ffmpeg-python, extensive logging

**3. `audio_transcription.py` (src/minutia/audio_transcription.py:1-66)**
- **Core Function**: `process_audio_files()` - transcribes audio using Whisper
- **Model Support**: Configurable Whisper models (base, small, medium, large)
- **Output Format**: Timestamped transcript files with `[start - end] text` format

**4. `transcript_merger.py` (src/minutia/transcript_merger.py:1-119)**
- **Core Function**: `process_transcripts()` - merges mic and desktop transcripts chronologically
- **Overlap Handling**: Optional overlap detection and merging
- **Output Format**: JSON with metadata and chronologically sorted segments

**5. `summarize_transcript.py` (src/minutia/summarize_transcript.py:1-243)**
- **AI Integration**: Anthropic Claude models for summarization
- **Functions**:
  - `generate_summary()` - single-pass summarization
  - `generate_long_summary()` - supports continuation for longer summaries
  - `estimate_tokens_and_price()` - cost estimation
- **Model Support**: Multiple Claude variants with pricing information

#### High-Level Functionality:
- **Meeting Recording Pipeline**: Complete MKV � Audio � Transcript � Summary workflow
- **Multi-track Audio**: Handles separate microphone and desktop audio streams
- **AI Summarization**: Advanced summarization with personal notes integration
- **Cost Management**: Token and pricing estimation for AI calls
- **Flexible Output**: Multiple output formats and naming strategies

#### Current Pain Points:
- **Hard-coded Parameters**: Track numbers, model names scattered throughout
- **Tight Coupling**: Modules directly import and call each other
- **Limited Extensibility**: Adding new transcription or summarization providers requires code changes
- **File Path Management**: Manual path construction and management
- **Configuration**: No centralized configuration management

## Modern Package Architecture

### Package Structure
```
src/minutia/
├── __init__.py              # Main API exports
├── config/
│   ├── __init__.py
│   ├── settings.py         # Pydantic-settings configuration classes
│   └── defaults.py         # Default configurations and constants
├── core/
│   ├── __init__.py
│   ├── pipelines.py        # Main pipeline orchestrators
│   ├── exceptions.py       # Custom exception hierarchy
│   └── types.py           # Common type definitions
├── providers/
│   ├── __init__.py
│   ├── base.py            # Abstract provider interfaces
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── whisper.py     # WhisperProvider
│   │   └── registry.py    # Provider registration
│   └── summarization/
│       ├── __init__.py
│       ├── claude.py      # ClaudeProvider
│       ├── ollama.py      # OllamaProvider
│       └── registry.py    # Provider registration
├── processing/
│   ├── __init__.py
│   ├── audio.py           # Audio extraction & preprocessing
│   ├── transcription.py   # Transcription orchestration
│   ├── merging.py         # Transcript merging logic
│   └── summarization.py   # Summarization orchestration
├── utils/
│   ├── __init__.py
│   ├── paths.py           # Smart filepath handling
│   ├── progress.py        # Rich progress bars & status
│   └── validation.py      # Input validation helpers
├── cli/
│   ├── __init__.py
│   ├── main.py           # Click CLI interface
│   ├── commands.py       # Individual CLI commands
│   └── rich_ui.py        # Rich formatting & progress
└── data/
    ├── __init__.py
    ├── models.py         # Data models (Results, Metadata, etc.)
    └── formats.py        # Output format handlers
```

### Core MVP Components

#### 1. Configuration Management with Pydantic-Settings (config/)
```python
# config/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Dict, Any, List

class AudioSettings(BaseSettings):
    mic_track: int = Field(3, description="Track number for microphone audio")
    desktop_track: int = Field(2, description="Track number for desktop audio") 
    extract_format: str = Field("wav", description="Audio extraction format")

class TranscriptionSettings(BaseSettings):
    provider: str = Field("whisper", description="Transcription provider")
    model: str = Field("base", description="Transcription model")
    language: Optional[str] = Field(None, description="Audio language (auto-detect if None)")
    provider_config: Dict[str, Any] = Field(default_factory=dict)

class SummarizationSettings(BaseSettings):
    provider: str = Field("claude", description="Summarization provider")
    model: str = Field("claude-3-5-sonnet", description="Summarization model")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    provider_config: Dict[str, Any] = Field(default_factory=dict)

class OutputSettings(BaseSettings):
    directory: Optional[Path] = Field(None, description="Output directory")
    naming_strategy: str = Field("timestamp", description="File naming strategy")
    formats: List[str] = Field(["json", "txt"], description="Output formats")
    create_subdirs: bool = Field(True, description="Create subdirectories")

class MinutiaSettings(BaseSettings):
    """Main configuration class supporting multiple sources"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='MINUTIA_',
        cli_parse_args=True,
        extra='ignore',
        case_sensitive=False
    )
    
    # Nested configurations
    audio: AudioSettings = Field(default_factory=AudioSettings)
    transcription: TranscriptionSettings = Field(default_factory=TranscriptionSettings)
    summarization: SummarizationSettings = Field(default_factory=SummarizationSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    
    # Global settings
    debug: bool = Field(False, description="Enable debug logging")
    log_level: str = Field("INFO", description="Logging level")

# Example usage in notebooks and CLI
# settings = MinutiaSettings()  # Loads from env vars, .env file, CLI args
# settings = MinutiaSettings(audio__mic_track=4)  # Override specific values
```

#### 2. Provider Architecture (providers/)
```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from pathlib import Path

class TranscriptionProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def transcribe(self, audio_path: Path, **kwargs) -> Dict[str, Any]:
        """Transcribe audio file and return structured result"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported audio formats"""
        pass

class SummarizationProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def summarize(self, transcript: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate summary from transcript"""
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript: str) -> Dict[str, Any]:
        """Estimate tokens and cost for summarization"""
        pass
```

#### 3. Pipeline Orchestration with Rich Progress (core/)
```python
# core/pipelines.py
from pathlib import Path
from typing import Optional, Union, List
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.text import Text

from ..config.settings import MinutiaSettings
from ..data.models import ProcessingResult
from ..utils.progress import create_progress_bar

class VideoPipeline:
    """Complete MKV to summary pipeline with Rich progress tracking"""
    
    def __init__(self, settings: MinutiaSettings):
        self.settings = settings
        self.console = Console()
    
    def process(self, 
                input_video: Path, 
                output_dir: Optional[Path] = None) -> ProcessingResult:
        """Process MKV file through complete pipeline with Rich UI"""
        
        # Display startup info
        self.console.print(Panel(
            f"[bold blue]Minutia Pipeline[/bold blue]\n"
            f"Input: {input_video}\n"
            f"Transcription: {self.settings.transcription.provider}/{self.settings.transcription.model}\n"
            f"Summarization: {self.settings.summarization.provider}/{self.settings.summarization.model}",
            title="Configuration"
        ))
        
        with create_progress_bar() as progress:
            # Step 1: Audio extraction
            audio_task = progress.add_task(
                "[cyan]Extracting audio tracks...", 
                total=100
            )
            audio_files = self._extract_audio(input_video, output_dir, progress, audio_task)
            
            # Step 2: Transcription  
            trans_task = progress.add_task(
                "[yellow]Transcribing audio...", 
                total=100
            )
            transcripts = self._transcribe_audio(audio_files, progress, trans_task)
            
            # Step 3: Merging
            merge_task = progress.add_task(
                "[magenta]Merging transcripts...", 
                total=100
            )
            merged_transcript = self._merge_transcripts(transcripts, progress, merge_task)
            
            # Step 4: Summarization
            summary_task = progress.add_task(
                "[green]Generating summary...", 
                total=100
            )
            result = self._generate_summary(merged_transcript, output_dir, progress, summary_task)
            
        # Display completion summary
        self.console.print(Panel(
            f"[bold green]✓ Processing Complete![/bold green]\n"
            f"Summary: {result.summary_path}\n"
            f"Transcript: {result.transcript_path}\n"
            f"Duration: {result.processing_time:.2f}s",
            title="Results"
        ))
        
        return result

class AudioPipeline:
    """Direct audio files to summary pipeline"""
    
    def __init__(self, settings: MinutiaSettings):
        self.settings = settings
        self.console = Console()
    
    def process(self, 
                audio_files: Union[Path, List[Path]], 
                output_dir: Optional[Path] = None) -> ProcessingResult:
        """Process audio file(s) directly to summary"""
        
        if isinstance(audio_files, Path):
            audio_files = [audio_files]
            
        self.console.print(Panel(
            f"[bold blue]Audio Pipeline[/bold blue]\n"
            f"Files: {len(audio_files)} audio file(s)\n"
            f"Transcription: {self.settings.transcription.provider}\n"
            f"Summarization: {self.settings.summarization.provider}",
            title="Configuration"
        ))
        
        with create_progress_bar() as progress:
            # Skip audio extraction, go straight to transcription
            trans_task = progress.add_task(
                "[yellow]Transcribing audio files...", 
                total=100
            )
            # Implementation continues...
        
        return ProcessingResult(...)
```

#### 4. Smart Filepath Handling (utils/)
```python
# utils/paths.py
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

class PathManager:
    def __init__(self, config: OutputConfig):
        self.config = config
    
    def resolve_output_dir(self, input_path: Path, custom_dir: Optional[Path] = None) -> Path:
        """Determine output directory with sensible defaults"""
        if custom_dir:
            return Path(custom_dir).resolve()
        
        if self.config.directory:
            return self.config.directory.resolve()
        
        # Default: create output dir next to input file
        return input_path.parent / f"{input_path.stem}_output"
    
    def generate_filename(self, base_name: str, extension: str, timestamp: bool = True) -> str:
        """Generate filename based on naming strategy"""
        if self.config.naming_strategy == "timestamp" and timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{ts}_{base_name}.{extension}"
        return f"{base_name}.{extension}"
```

#### 5. Enhanced CLI with Pydantic-Settings Integration (cli/)
```python
# cli/main.py
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..config.settings import MinutiaSettings
from ..core.pipelines import VideoPipeline, AudioPipeline
from ..providers.transcription.registry import list_transcription_providers
from ..providers.summarization.registry import list_summarization_providers

def create_settings_from_cli(**overrides) -> MinutiaSettings:
    """Create settings with CLI overrides"""
    return MinutiaSettings(**overrides)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--log-level', default='INFO', help='Set logging level')
@click.pass_context
def main(ctx, debug, log_level):
    """Minutia: Meeting transcription and summarization"""
    ctx.ensure_object(dict)
    ctx.obj['global_settings'] = {'debug': debug, 'log_level': log_level}

@main.command()
@click.argument('input_video', type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path), help='Output directory')
@click.option('--transcription-model', help='Transcription model to use')
@click.option('--summarization-model', help='Summarization model to use')
@click.option('--mic-track', type=int, help='Microphone track number')
@click.option('--desktop-track', type=int, help='Desktop audio track number')
@click.pass_context
def process_video(ctx, input_video: Path, output_dir: Optional[Path], 
                 transcription_model: Optional[str], summarization_model: Optional[str],
                 mic_track: Optional[int], desktop_track: Optional[int]):
    """Process MKV video file to summary"""
    
    # Build settings with CLI overrides
    settings_overrides = {**ctx.obj['global_settings']}
    
    if transcription_model:
        settings_overrides['transcription__model'] = transcription_model
    if summarization_model:
        settings_overrides['summarization__model'] = summarization_model
    if mic_track:
        settings_overrides['audio__mic_track'] = mic_track
    if desktop_track:
        settings_overrides['audio__desktop_track'] = desktop_track
    if output_dir:
        settings_overrides['output__directory'] = output_dir
    
    settings = create_settings_from_cli(**settings_overrides)
    
    # Run pipeline
    pipeline = VideoPipeline(settings)
    result = pipeline.process(input_video, output_dir)

@main.command()
@click.argument('audio_files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path), help='Output directory')
@click.option('--transcription-model', help='Transcription model to use')
@click.option('--summarization-model', help='Summarization model to use')
@click.pass_context
def process_audio(ctx, audio_files: tuple[Path, ...], output_dir: Optional[Path],
                 transcription_model: Optional[str], summarization_model: Optional[str]):
    """Process audio files directly to summary"""
    
    if not audio_files:
        console = Console()
        console.print("[red]Error: No audio files provided[/red]")
        raise click.Abort()
    
    # Build settings with CLI overrides (similar to process_video)
    settings_overrides = {**ctx.obj['global_settings']}
    if transcription_model:
        settings_overrides['transcription__model'] = transcription_model
    if summarization_model:
        settings_overrides['summarization__model'] = summarization_model
    if output_dir:
        settings_overrides['output__directory'] = output_dir
    
    settings = create_settings_from_cli(**settings_overrides)
    
    # Run pipeline
    pipeline = AudioPipeline(settings)
    result = pipeline.process(list(audio_files), output_dir)

@main.command()
def list_providers():
    """List available transcription and summarization providers"""
    console = Console()
    
    # Transcription providers table
    trans_table = Table(title="Transcription Providers", show_header=True, header_style="bold cyan")
    trans_table.add_column("Provider", style="cyan", width=15)
    trans_table.add_column("Models", style="green")
    trans_table.add_column("Description", style="dim white")
    
    for provider, info in list_transcription_providers().items():
        trans_table.add_row(
            provider, 
            ", ".join(info['models']), 
            info.get('description', '')
        )
    
    console.print(trans_table)
    console.print()
    
    # Summarization providers table  
    sum_table = Table(title="Summarization Providers", show_header=True, header_style="bold magenta")
    sum_table.add_column("Provider", style="magenta", width=15)
    sum_table.add_column("Models", style="green")
    sum_table.add_column("Description", style="dim white")
    
    for provider, info in list_summarization_providers().items():
        sum_table.add_row(
            provider,
            ", ".join(info['models']),
            info.get('description', '')
        )
    
    console.print(sum_table)

@main.command()
def show_config():
    """Display current configuration"""
    console = Console()
    settings = MinutiaSettings()
    
    # Create config display panel
    config_text = f"""[bold cyan]Audio Settings:[/bold cyan]
  Mic Track: {settings.audio.mic_track}
  Desktop Track: {settings.audio.desktop_track}
  Extract Format: {settings.audio.extract_format}

[bold yellow]Transcription Settings:[/bold yellow]
  Provider: {settings.transcription.provider}
  Model: {settings.transcription.model}
  Language: {settings.transcription.language or 'auto-detect'}

[bold green]Summarization Settings:[/bold green]
  Provider: {settings.summarization.provider}
  Model: {settings.summarization.model}

[bold blue]Output Settings:[/bold blue]
  Directory: {settings.output.directory or 'auto-generated'}
  Naming Strategy: {settings.output.naming_strategy}
  Formats: {', '.join(settings.output.formats)}
  Create Subdirs: {settings.output.create_subdirs}

[bold white]Global Settings:[/bold white]
  Debug: {settings.debug}
  Log Level: {settings.log_level}"""
    
    console.print(Panel(config_text, title="Current Configuration", border_style="blue"))
    
    console.print(f"\n[dim]Configuration loaded from:")
    console.print(f"  • Environment variables (MINUTIA_*)")
    console.print(f"  • .env file (if present)")
    console.print(f"  • CLI arguments")
    console.print(f"  • Default values[/dim]")
```

## Project Dependencies

Here is some more detail on the desired packages and libraries to use

### **Core Dependencies**
- **click** - CLI framework with advanced context/group features
- **pydantic** - Data validation and models  
- **pydantic-settings** - Configuration management (env vars, .env files, CLI args)
- **rich** - Terminal UI, progress bars, formatted output
- **anthropic** - Claude AI API client
- **openai-whisper** - Audio transcription
- **ffmpeg-python** - Audio/video processing

### **Development Tools**
- **ruff** - Fast linter/formatter (replaces black + flake8)
- **pytest** - Testing framework
- **mypy** - Type checking

### **Optional Providers (Future)**
- **ollama** - Local LLM integration for summarization
- **requests** - HTTP client for additional API integrations

### Documentation links

pydantic: https://ai.pydantic.dev/llms.txt
pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/


rich: https://rich.readthedocs.io/en/latest/
click: https://click.palletsprojects.com/en/stable/api/

pytest How to guides: https://docs.pytest.org/en/stable/how-to/index.html#how-to-guides
pyterst API reference: https://docs.pytest.org/en/stable/reference/index.html

anthropic docs: https://docs.claude.com/en/api/messages
anthropic api: https://github.com/anthropics/anthropic-sdk-python/blob/main/api.md



## Implementation Priorities and roadmap

1. **Core Infrastructure** (Week 1)
   - Pydantic-settings configuration classes
   - Provider base classes & registry system
   - Basic pipeline structure with Rich integration

2. **Provider Implementation** (Week 2) 
   - WhisperProvider with model validation
   - ClaudeProvider with cost estimation
   - Provider discovery & registration system

3. **Pipeline Logic** (Week 3)
   - VideoPipeline with Rich progress tracking
   - AudioPipeline for direct audio processing
   - Error handling & validation with Rich formatting

4. **CLI & User Experience** (Week 4)
   - Enhanced CLI with pydantic-settings integration
   - Configuration display commands
   - Path management utilities with Rich feedback

5. **Testing & Polish** (Week 5)
   - Unit tests for core components
   - Integration tests for pipelines  
   - Ruff formatting setup
   - Documentation & examples