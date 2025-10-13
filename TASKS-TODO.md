# Minutia Project Tasks & TODO

## High Priority - Code Quality & Cleanup

### 🧹 Import Cleanup (Critical)
- [ ] **video_extraction.py**: Remove unused imports (whisper, pandas, numpy, transformers, torch, openai, anthropic, pydantic, instructor, dotenv)
- [ ] **audio_transcription.py**: Analyze and clean unused imports
- [ ] **summarize_transcript.py**: Analyze and clean unused imports  
- [ ] **transcript_merger.py**: Analyze and clean unused imports
- [ ] Fix import sorting and formatting across all modules

### 🐛 Code Issues from Diagnostics
- [ ] **video_extraction.py**: Fix unused loop variable `stream` on line 72
- [ ] **video_extraction.py**: Remove blank lines with whitespace
- [ ] **video_extraction.py**: Add newline at end of file
- [ ] Run `uv run ruff check --fix .` to auto-fix formatting issues

### 🧪 Testing Infrastructure  
- [ ] Set up basic pytest structure with test files
- [ ] Create unit tests for core functions:
  - [ ] `process_mkv_file()` function
  - [ ] `identify_audio_tracks()` function  
  - [ ] `extract_audio_track()` function
- [ ] Add integration tests for CLI commands
- [ ] Set up test fixtures and mock data

## Medium Priority - Feature Development

### 📁 Project Structure
- [ ] Move Jupyter notebooks to `notebooks/` directory
- [ ] Organize archive data and recordings in proper structure
- [ ] Create proper data directory structure
- [ ] Add `.gitignore` for build artifacts, .venv, __pycache__, etc.

### 📖 Documentation
- [ ] Create comprehensive README.md
- [ ] Add docstring documentation to all functions
- [ ] Create API documentation
- [ ] Add usage examples and tutorials

### 🔧 CLI Enhancements
- [ ] Add proper error handling and user-friendly error messages
- [ ] Add progress bars for long-running operations
- [ ] Add configuration file support
- [ ] Add verbose/quiet output options

## Low Priority - Polish & Optimization

### 🎯 Performance 
- [ ] Analyze dependency usage - some imports might be optional
- [ ] Optimize audio processing pipeline
- [ ] Add async support for I/O operations
- [ ] Profile memory usage during large file processing

### 🔒 Security & Best Practices
- [ ] Add input validation for file paths and parameters
- [ ] Secure API key handling
- [ ] Add rate limiting for API calls
- [ ] Add proper logging configuration

### 🚀 Packaging & Distribution
- [ ] Add build scripts and CI/CD
- [ ] Create Docker container
- [ ] Add installation instructions
- [ ] Prepare for PyPI publication

## Future Enhancements

### 🎵 Audio Processing
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

## Working Notes

### Current Status
✅ **COMPLETED**: Successfully converted to uv project structure with proper packaging
- All Python modules moved to `src/minutia/` 
- Dependencies migrated to pyproject.toml
- CLI entry point working
- Development tooling configured (ruff, pytest)

### Next Chunk Recommendations
1. **Start with Code Cleanup** - Fix the import issues and linting errors first
2. **Add Basic Tests** - Set up pytest structure and basic unit tests  
3. **Documentation** - Create README and improve docstrings