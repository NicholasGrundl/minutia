# Test Infrastructure Refactor Plan

## Overview

This document outlines the comprehensive plan for rebuilding and overhauling the test suite and DevOps test setup for Minutia. The strategy focuses on creating a robust three-tier testing architecture with real fixtures and comprehensive coverage.

## Goals

- **Stability**: Build unit tests for core services and data classes to ensure stability during refactoring
- **Real-world validation**: Integration tests that run on REAL .mkv files and audio
- **Fixture infrastructure**: Helper scripts to create new fixtures and intermediate states
- **Regression prevention**: Comprehensive test coverage to prevent breaking changes
- **Performance tiers**: Fast unit tests for development, slower integration tests for validation

## Testing Architecture (from design.md)

### Three-Tier Test Strategy

**Unit Tests** (< 1s each)
- Mocked dependencies
- Test individual functions and data structures
- Fast feedback for development
- Target: `pytest -m unit`

**Integration Tests** (< 30s each)  
- Real Whisper tiny model
- Real FFmpeg with small test files
- Mocked API calls (Anthropic)
- Target: `pytest -m "unit or integration"`

**Slow Tests** (full pipeline)
- End-to-end with actual models and API calls
- Real .mkv files through complete pipeline
- Golden sample validation
- Target: `pytest -m "unit or integration or slow"`

### Resource Management Strategy

**Session-scoped fixtures**: Expensive resources (Whisper models, test audio files)
**Module-scoped fixtures**: Shared test data (sample transcripts)  
**Function-scoped fixtures**: Isolated run directories for test independence

## Revised Development Phases

### Phase 1: Fixture Generation & Test Infrastructure (2-3 days) ⭐ CRITICAL FOUNDATION

**Priority: HIGHEST - Everything else depends on this**

#### 1.1 Test Directory Structure
Create the complete test directory structure following design.md:

```
tests/
├── conftest.py              # Global fixtures and configuration
├── fixtures/                # Test data and golden samples
│   ├── audio/               # Small audio files for testing
│   ├── video/               # Small video files for testing
│   ├── transcripts/         # Known-good transcript outputs
│   └── golden_samples/      # Complete pipeline outputs for regression
├── unit/                    # Fast tests by module (< 1s each)
│   ├── test_models.py       # RunPaths, PipelineConfig, etc.
│   ├── test_config.py       # Configuration loading and validation
│   ├── test_validation.py   # Input validation and schema validation
│   └── steps/               # Individual pipeline step tests
│       ├── test_video_extraction.py
│       ├── test_audio_transcription.py  
│       ├── test_transcript_merging.py
│       └── test_summary_generation.py
├── integration/             # Medium tests with real models (< 30s)
│   ├── test_whisper_integration.py    # Real Whisper tiny model tests
│   ├── test_ffmpeg_integration.py     # Real FFmpeg with small files
│   └── test_pipeline_steps.py         # Step-by-step with real data
├── slow/                    # Full pipeline tests
│   └── test_end_to_end.py   # Complete .mkv → summary pipeline
└── scripts/                 # Helper scripts (in tests for now, may move)
    ├── generate_test_fixtures.py      # Create small test files
    ├── create_golden_samples.py       # Generate known-good outputs
    └── validate_golden_samples.py     # Regression testing utility
```

#### 1.2 Fixture Generation Scripts

**scripts/generate_test_fixtures.py**
- Extract 10-30 second clips from real recordings
- Create multiple scenarios:
  - `sample_short.mkv`: Clear speech, minimal background
  - `sample_overlap.mkv`: Mic + desktop audio with overlaps
  - `sample_quiet.mkv`: Very quiet audio (edge case)
  - `sample_noisy.mkv`: Background noise/music
- Ensure FFmpeg can extract multiple audio tracks
- Validate resulting files have expected properties

**scripts/create_golden_samples.py**
- Run existing CreateTranscriptProd.ipynb on generated fixtures
- Capture all intermediate and final outputs:
  - Extracted audio files
  - Individual transcript JSON files
  - Merged transcript JSON
  - Summary text (if API key available)
- Store as known-good baseline for regression testing
- Document exact pipeline parameters used


#### 1.3 Core Test Infrastructure

**conftest.py Setup**
```python
import pytest
from pathlib import Path
import json

@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session") 
def whisper_tiny_model():
    """Load tiny Whisper model once per test session."""
    import whisper
    model = whisper.load_model("tiny")
    yield model
    del model

@pytest.fixture(scope="session")
def test_video_files(test_fixtures_dir):
    """Load test video files created by fixture generation scripts."""
    video_dir = test_fixtures_dir / "video"
    return {
        "short": video_dir / "sample_short.mkv",
        "overlap": video_dir / "sample_overlap.mkv", 
        "quiet": video_dir / "sample_quiet.mkv"
    }

@pytest.fixture(scope="session")
def golden_samples(test_fixtures_dir):
    """Load golden sample outputs for regression testing."""
    golden_dir = test_fixtures_dir / "golden_samples"
    samples = {}
    for sample_dir in golden_dir.iterdir():
        if sample_dir.is_dir():
            samples[sample_dir.name] = sample_dir
    return samples

@pytest.fixture
def isolated_tmp_dir(tmp_path):
    """Create isolated temporary directory for each test."""
    return tmp_path

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API for unit/integration tests."""
    # Implementation for mocking API calls
    pass
```

#### 1.4 pytest Configuration

**pytest.ini**
```ini
[tool:pytest]
markers =
    unit: Unit tests (fast, < 1s each)
    integration: Integration tests (medium, < 30s)
    slow: Slow tests (full pipeline, manual runs)
    
addopts = -n auto --tb=short -v
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Phase 2: Core Model Testing (2-3 days)

**Focus**: Test foundational data structures and configuration with real fixtures

#### 2.1 RunPaths Testing (test_models.py)
- Test directory creation and collision handling
- Test path resolution with different input types
- Test validation of input files and output directories
- Use real fixture files from Phase 1

#### 2.2 Configuration Testing (test_config.py)  
- Test precedence: CLI > env vars > config file > defaults
- Test config file discovery and loading
- Test API key handling and validation
- Test error cases and edge conditions

#### 2.3 Data Serialization Testing
- Test PipelineConfig serialization for state persistence
- Test transcript JSON schema validation
- Test metadata structure consistency

### Phase 3: Pipeline Step Testing (3-4 days)

**Focus**: Test individual pipeline steps with real fixtures and models

#### 3.1 Video Extraction Testing (test_video_extraction.py)
- Use real .mkv fixtures from Phase 1
- Test track detection and extraction
- Test error handling for missing tracks
- Test audio file validation and format

#### 3.2 Audio Transcription Testing (test_audio_transcription.py)
- Use real Whisper tiny model (integration level)
- Test with various audio qualities from fixtures
- Test JSON output format and schema
- Test error handling for corrupted audio

#### 3.3 Transcript Merging Testing (test_transcript_merging.py)
- Use real transcript files generated by Phase 1
- Test chronological ordering and overlap detection
- Test metadata generation and consistency
- Test edge cases (empty transcripts, timing overlaps)

#### 3.4 Summary Generation Testing (test_summary_generation.py)
- Mock Anthropic API for fast testing
- Test prompt generation and token estimation
- Test error handling for API failures
- Test output format and validation

### Phase 4: End-to-End Testing (1-2 days) SIMPLIFIED

**Focus**: Full pipeline validation using golden samples

#### 4.1 Orchestrator Testing (STUB ONLY)
- Create placeholder test files
- Add TODO comments for future state management testing
- Basic structure without implementation

#### 4.2 State Management Testing (STUB ONLY)  
- Create placeholder test files
- Add TODO comments for resume-from-failure testing
- Basic structure without implementation

#### 4.3 End-to-End Slow Tests (MAIN FOCUS)
```python
@pytest.mark.slow
def test_complete_pipeline_with_golden_samples(test_video_files, golden_samples, tmp_path):
    """
    Complete pipeline test: MKV → transcripts → summary.
    
    Uses real fixtures and compares against golden samples for regression detection.
    """
    # Run complete pipeline on sample_short.mkv
    # Compare outputs against golden samples
    # Allow for variation in transcription but validate structure
    # Validate all intermediate files are created correctly
```

## Makefile Integration

The existing Makefile is already well-prepared for this strategy:

```bash
# Development workflow
make test-unit           # Fast feedback (< 10s total)
make test-integration    # Pre-commit validation (< 2m total)  
make test-all           # Full validation including slow tests

# New additions needed
make generate-fixtures   # Run Phase 1 fixture generation scripts
make update-golden       # Regenerate golden samples from current pipeline
make test-regression     # Compare current output vs golden samples
```

**Additional Makefile targets to add:**

```makefile
.PHONY: generate-fixtures
generate-fixtures:
	@echo "Generating test fixtures from real recordings..."
	uv run python tests/scripts/generate_test_fixtures.py

.PHONY: update-golden
update-golden:
	@echo "Updating golden samples with current pipeline..."
	uv run python tests/scripts/create_golden_samples.py

.PHONY: test-regression
test-regression:
	@echo "Running regression tests against golden samples..."
	uv run python tests/scripts/validate_golden_samples.py
```

## Key Success Criteria

### Phase 1 Completion Criteria
- [ ] Complete test directory structure exists
- [ ] 3-4 small test .mkv files with different characteristics
- [ ] Golden sample outputs generated for each test file
- [ ] conftest.py with session-scoped fixtures working
- [ ] `make generate-fixtures` command working

### Phase 2 Completion Criteria  
- [ ] RunPaths class fully tested with real file validation
- [ ] Configuration loading tested with all precedence rules
- [ ] Data serialization working and tested
- [ ] All unit tests run in < 10s total

### Phase 3 Completion Criteria
- [ ] Each pipeline step tested individually with real data
- [ ] Integration tests use real Whisper tiny model
- [ ] Idempotency and error handling verified
- [ ] Integration tests run in < 2m total

### Phase 4 Completion Criteria
- [ ] Orchestrator and state management tests stubbed
- [ ] One comprehensive end-to-end slow test working
- [ ] Golden sample regression validation working
- [ ] Full test suite provides regression protection

## Future Enhancements (Post-Plan)

After this plan is complete, the test infrastructure will support:

- **Advanced orchestration testing**: State persistence, resume-from-failure
- **Performance benchmarking**: Track processing times and resource usage
- **API cost tracking**: Monitor Anthropic API usage in tests
- **Continuous integration**: Automated testing on different OS/Python versions
- **Fixture expansion**: Easy addition of new test scenarios

## Dependencies & Prerequisites

### External Dependencies
- `pytest` with markers and parallel execution
- `whisper` tiny model for integration tests
- `ffmpeg` for real audio/video processing
- Real .mkv recording files as source for fixtures

### Existing Code Dependencies  
- Working CreateTranscriptProd.ipynb pipeline
- Current video_extraction.py, audio_transcription.py modules
- Existing CLI interface for baseline functionality

### Development Environment
- UV package management working
- Makefile task runner configured
- API keys available for golden sample generation

## Risk Mitigation

**Risk**: Fixture generation requires large source files
**Mitigation**: Use existing test recordings, create minimal viable fixtures first

**Risk**: Real model testing is slow
**Mitigation**: Use tiny models, small fixtures, and session-scoped loading

**Risk**: API costs for golden sample generation
**Mitigation**: Generate samples once, cache results, mock APIs in regular tests

**Risk**: Test maintenance burden
**Mitigation**: Focus on regression prevention over exhaustive coverage, clear test organization

## Coordination with Existing Work

This testing plan complements the ongoing refactoring work:

- **Non-disruptive**: Tests don't modify existing working code
- **Regression protection**: Ensures refactoring doesn't break functionality  
- **Foundation for new code**: Provides testing patterns for new modules
- **Documentation**: Tests serve as executable documentation of expected behavior

The plan prioritizes creating a solid foundation (Phase 1) that unlocks effective testing for all subsequent development work.