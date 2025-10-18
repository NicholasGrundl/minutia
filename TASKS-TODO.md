# Minutia Project Tasks & TODO

*Implementation follows design/design-test-refactor-plan.md for comprehensive test infrastructure*

## Current Priority: Test Infrastructure Implementation

### Overview
Focus has shifted to building comprehensive test infrastructure before further feature development. This provides regression protection during refactoring and establishes quality patterns for future work.

## Phase 1: Test Foundation & Fixture Generation (2-3 days) ⭐ COMPLETED

**Priority: COMPLETED ✅ - Fixtures migrated from +outputs to scenario-based structure**

### 🏗️ Test Directory Structure ✅ COMPLETED
- [x] Create complete test directory structure following design-test-refactor-plan.md
- [x] Set up `tests/conftest.py` with global fixtures and pytest configuration
- [x] Create subdirectories: `fixtures/`, `unit/`, `integration/`, `slow/`, `scripts/`
- [x] Add `pytest.ini` with markers for unit/integration/slow tests

### 🎬 Fixture Generation & Organization ✅ COMPLETED
- [x] ~~Implement `tests/scripts/generate_test_fixtures.py` to extract 10-30s clips from real recordings~~ **REPLACED**: Used `CreateNewFixtureSet.ipynb` to generate complete fixtures
- [x] Create diverse test scenarios: microphone_only, noisy_microphone, podcast_desktop, youtube_desktop
- [x] Ensure all fixtures have multiple audio tracks extractable by FFmpeg
- [x] Validate fixture properties and document characteristics
- [x] **NEW**: Migrate +outputs to scenario-based structure with pipeline stage organization
- [x] **NEW**: Create comprehensive metadata.json for each scenario and master registry

### 🏆 Golden Sample Generation ✅ COMPLETED
- [x] ~~Implement `tests/scripts/create_golden_samples.py` using existing CreateTranscriptProd.ipynb~~ **REPLACED**: Used `CreateNewFixtureSet.ipynb` for end-to-end golden samples
- [x] Generate known-good outputs for all fixtures: audio files, transcripts, merged JSON, summaries
- [x] Store outputs as regression baseline with documented pipeline parameters (in scenario metadata)
- [x] **NEW**: Organized golden samples by pipeline stage (01_extracted → 04_summarized)
- [ ] Create validation utilities for comparing test outputs against golden samples

### ⚙️ Core Test Infrastructure
- [ ] Set up session-scoped fixtures for Whisper models and test files
- [ ] Configure module-scoped fixtures for shared test data
- [ ] Create function-scoped fixtures for isolated temporary directories
- [ ] Implement Anthropic API mocking for unit/integration tests

### 📋 Makefile Integration
- [ ] Add `make generate-fixtures` command (update to use new structure)
- [ ] Add `make update-golden` command for regenerating samples
- [ ] Add `make test-regression` for golden sample validation
- [ ] Update existing test commands to use new architecture

### 🔄 Fixture Refactoring Tasks ⭐ NEW PRIORITY
- [ ] Remove obsolete notebooks: `DEV_create_complete_fixtures.ipynb`, `DEV_generate_test_fixtures_simple*.ipynb`
- [ ] Extract reusable code from `CreateNewFixtureSet.ipynb` to `tests/scripts/utilities.py`
- [ ] Create standalone script `tests/scripts/generate_complete_fixtures.py` based on notebook
- [ ] Update `simple/` fixtures to use new structure (create small unit test clips)

## Phase 2: Core Model & Configuration Testing (2-3 days)

### 📁 RunPaths & Data Structure Testing
- [ ] Implement `tests/unit/test_models.py` for RunPaths class
- [ ] Test directory creation, collision handling, path resolution
- [ ] Test validation with real fixture files from Phase 1
- [ ] Test PipelineConfig and PipelineResult serialization

### ⚙️ Configuration System Testing
- [ ] Implement `tests/unit/test_config.py` for configuration loading
- [ ] Test precedence: CLI flags > env vars > config file > defaults
- [ ] Test config file discovery and API key handling
- [ ] Test error cases and validation edge conditions

### 🎯 Performance Target
- [ ] Ensure all unit tests complete in < 10s total
- [ ] Optimize fixtures and test setup for fast feedback

## Phase 3: Pipeline Step Testing (3-4 days)

### 🎥 Video Extraction Testing
- [ ] Implement `tests/integration/test_video_extraction.py`
- [ ] Test with real .mkv fixtures from Phase 1
- [ ] Test track detection, extraction, and audio file validation
- [ ] Test error handling for missing tracks and corrupted files

### 🎤 Audio Transcription Testing
- [ ] Implement `tests/integration/test_audio_transcription.py`
- [ ] Use real Whisper tiny model for integration tests
- [ ] Test various audio qualities and edge cases from fixtures
- [ ] Test JSON output format and schema validation

### 📝 Transcript Merging Testing
- [ ] Implement `tests/integration/test_transcript_merging.py`
- [ ] Use real transcript files generated in Phase 1
- [ ] Test chronological ordering and overlap detection
- [ ] Test metadata generation and consistency

### 🤖 Summary Generation Testing
- [ ] Implement `tests/integration/test_summary_generation.py`
- [ ] Mock Anthropic API for fast, cost-free testing
- [ ] Test prompt generation and token estimation
- [ ] Test error handling and output validation

### 🎯 Performance Target
- [ ] Ensure integration tests complete in < 2m total
- [ ] Use session-scoped model loading for efficiency

## Phase 4: End-to-End & Regression Testing (1-2 days)

### 🔄 Future Architecture Stubs
- [ ] Create placeholder tests for PipelineOrchestrator (future state management)
- [ ] Add TODO comments for resume-from-failure testing
- [ ] Basic structure for state persistence testing

### 🧪 Comprehensive End-to-End Testing
- [ ] Implement `tests/slow/test_end_to_end.py` for complete pipeline
- [ ] Test MKV → transcripts → summary flow with real fixtures
- [ ] Compare outputs against golden samples for regression detection
- [ ] Validate all intermediate files and final artifacts

### 📊 Regression Protection
- [ ] Implement golden sample comparison utilities
- [ ] Add tolerance for acceptable variation in transcription
- [ ] Validate structural consistency across pipeline changes
- [ ] Document regression criteria and thresholds

---

## Future Feature Development (Deferred)

*These features will be implemented after test infrastructure is complete*

### Phase 7: Rich CLI Interface (Post-Testing)
- [ ] Replace simple progress output with rich progress bars
- [ ] Add styled panels for status and artifact locations
- [ ] Implement sophisticated CLI UX patterns with error formatting

### Phase 8: Resume-From-Failure (Post-Testing)
- [ ] Add PipelineState persistence to run directory
- [ ] Implement state serialization helpers and JSON storage
- [ ] Add idempotency checks to each pipeline step
- [ ] Implement `resume_from_failure()` method

### Documentation & Polish
- [ ] Create comprehensive README.md
- [ ] Add docstring documentation to all functions
- [ ] Create API documentation and usage examples

### Performance & Optimization
- [ ] Analyze dependency usage for optional imports
- [ ] Optimize audio processing pipeline
- [ ] Add async support for I/O operations
- [ ] Profile memory usage during large file processing

### Packaging & Distribution
- [ ] Add build scripts and CI/CD
- [ ] Create Docker container
- [ ] Add installation instructions
- [ ] Prepare for PyPI publication

### Audio Processing Enhancements
- [ ] Support for more audio formats
- [ ] Audio quality analysis and enhancement
- [ ] Speaker diarization improvements
- [ ] Real-time processing capabilities

### AI/ML Features
- [ ] Improved summarization with different models
- [ ] Custom model fine-tuning options
- [ ] Sentiment analysis of meetings
- [ ] Action item extraction

---

## Implementation Strategy

### Current Status
✅ **FOUNDATION COMPLETE**: Working CLI with pipeline orchestration
- Complete uv project structure with proper packaging
- All core pipeline functionality working (Phases 1-6 from previous plan)
- Unified logging, configuration, and data structures in place
- JSON-structured data formats implemented

### Test Infrastructure Strategy
- **Total Timeline**: ~1-2 weeks of focused work (4 phases)
- **Key Principle**: Build robust testing foundation before further feature development
- **Dependencies**: Phase 1 is critical foundation, Phases 2-3 can run in parallel, Phase 4 depends on 1-3
- **Regression Protection**: Every change validated against golden samples

### Success Criteria
**Phase 1**: Complete test structure, fixtures, golden samples, < 1s setup time
**Phase 2**: Core models fully tested, configuration validated, < 10s unit tests
**Phase 3**: All pipeline steps tested with real data, < 2m integration tests
**Phase 4**: End-to-end regression protection, golden sample validation working

### Quality Gates
- All tests must pass before merging any code changes
- Golden sample validation prevents breaking changes
- Performance targets ensure fast development feedback
- Real fixture testing catches edge cases early
