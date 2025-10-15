# Minutia Project Tasks & TODO

*Implementation follows design/design.md phased approach with MVP focus*

## Phase 1: Foundation & Verification (Critical Path - MVP)

### 🔍 Pipeline Verification & Baseline Script
- [x] Verify CreateTranscriptProd.ipynb runs end-to-end with test recording
- [x] Convert notebook cells to standalone Python script preserving all working logic
- [x] Create basic integration test (smoke test) that runs full pipeline and validates outputs
- [x] Document current advanced features (personal notes, cost estimation, auto-filenames)

### 🧹 Critical Code Cleanup
- [x] **video_extraction.py**: Remove unused imports (whisper, pandas, numpy, transformers, torch, openai, anthropic, pydantic, instructor, dotenv)
- [x] **video_extraction.py**: Fix unused loop variable `stream` on line 72
- [x] **video_extraction.py**: Remove blank lines with whitespace and add newline at end
- [x] Run `uv run ruff check --fix .` to auto-fix formatting issues
- [x] Move notebooks to `notebooks/` directory

## Phase 2: Core Data Structures (MVP - Foundation)

### 📁 RunPaths & Path Management 
- [x] Implement RunPaths dataclass with factory methods (`from_video_input`, `from_audio_inputs`)
- [x] Add directory collision handling and validation
- [x] Create PipelineConfig and PipelineResult data structures
- [x] Migrate existing modules to use RunPaths instead of ad-hoc path construction
- [x] Add unit tests for path resolution and data structures

## Phase 3: Pipeline Architecture (MVP - Core)

### ⚙️ Basic Pipeline Orchestration
- [x] Implement PipelineOrchestrator class with callback-based progress reporting
- [x] Add basic step execution with exception handling and error messages
- [x] Create step enumeration and execution framework
- [x] Add basic state tracking (defer full resume-from-failure to Phase 8)
- [x] Add unit tests for orchestrator logic

## Phase 4: Logging & Configuration (MVP - Infrastructure)

### 📝 Unified Logging System
- [x] Replace multiple basic loggers with unified loguru setup
- [x] Add contextual fields (`step`, `input_file`, `run_root`) for log correlation
- [x] Configure simple file sink for run directory and colored stderr sink
- [x] Integrate with pipeline orchestrator for structured logging

### ⚙️ Basic Configuration System
- [x] Implement basic configuration system with environment variable support
- [x] Add configuration validation and API key handling
- [x] Add `.env` file support for configuration
- [x] Secure API key handling with fallback chain

## Phase 5: Simple CLI Wrapper (MVP - Interface)

### 🖥️ Basic CLI Interface
- [x] Wrap pipeline orchestrator with Click CLI interface
- [x] Add simple progress output using print/logging (not rich UI yet)
- [x] Display final artifact locations on completion
- [x] Map pipeline exceptions to clear error messages
- [x] Preserve all current CLI arguments and functionality

## Phase 6: JSON Data Formats (Post-MVP)

### 📄 Structured Data Migration
- [x] Convert individual transcripts from plain text to structured JSON
- [x] Update merged transcript format with metadata section
- [x] Add run metadata file generation
- [x] Update transcript merger to handle JSON inputs/outputs
- [x] Ensure backward compatibility during transition

## Phase 7: Rich CLI Interface (Post-MVP)

### 🎨 Enhanced User Experience
- [ ] Replace simple progress output with rich progress bars
- [ ] Add styled panels for status and artifact locations
- [ ] Implement sophisticated CLI UX patterns with error formatting
- [ ] Add interactive elements and enhanced user experience

## Phase 8: Resume-From-Failure (Post-MVP)

### 🔄 State Management & Recovery
- [ ] Add PipelineState persistence to run directory
- [ ] Implement state serialization helpers and JSON storage
- [ ] Add idempotency checks to each pipeline step with artifact validation
- [ ] Implement `resume_from_failure()` method with proper state loading

## Deferred Tasks (Future Consideration)

### 📖 Documentation (Lower Priority)
- [ ] Create comprehensive README.md (design.md already comprehensive)
- [ ] Add docstring documentation to all functions
- [ ] Create API documentation
- [ ] Add usage examples and tutorials

### 🎯 Performance & Optimization
- [ ] Analyze dependency usage - some imports might be optional
- [ ] Optimize audio processing pipeline
- [ ] Add async support for I/O operations
- [ ] Profile memory usage during large file processing

### 🚀 Packaging & Distribution
- [ ] Add build scripts and CI/CD
- [ ] Create Docker container
- [ ] Add installation instructions
- [ ] Prepare for PyPI publication

### 🎵 Audio Processing Enhancements
- [ ] Support for more audio formats
- [ ] Audio quality analysis and enhancement
- [ ] Speaker diarization improvements
- [ ] Real-time processing capabilities

### 🤖 AI/ML Features
- [ ] Improved summarization with different models
- [ ] Custom model fine-tuning options
- [ ] Sentiment analysis of meetings
- [ ] Action item extraction

---

## Implementation Notes

### Current Status
✅ **COMPLETED**: Successfully converted to uv project structure with proper packaging
- All Python modules moved to `src/minutia/`
- Dependencies migrated to pyproject.toml
- CLI entry point working
- Development tooling configured (ruff, pytest)

### MVP Strategy
- **Total MVP Timeline**: ~1 week of focused work (Phases 1-5)
- **Key Principle**: Preserve working functionality first, enhance second
- **Dependencies**: Phase 1 is sequential, Phases 2-4 can run in parallel, Phase 5 depends on 2-4
- **Testing**: Start with minimal smoke test, expand to comprehensive testing post-MVP

### Phase Boundaries
- **MVP (Phases 1-5)**: Essential deliverables for refactored CLI with basic functionality
- **Post-MVP (Phases 6-8)**: Enhanced features building on proven MVP foundation
- **Future**: Advanced features and optimizations based on user feedback
