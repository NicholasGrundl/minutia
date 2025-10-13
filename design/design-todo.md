# Design Document TODO: Areas Requiring Implementation Detail

## Overview
This document captures gaps and areas needing expansion in the current design document (`design.md`) based on comparison with the planning document. Use this as a checklist to incrementally improve the design to be implementation-ready.

## Critical Missing Implementation Details

### **1. __meta: [Data Models Schema]** - `data/models.py`
**Status**: 🔴 Critical Gap  
**Current**: Mentions `ProcessingResult`, `TranscriptSegment` but no concrete schemas  
**Needed**: Complete data model definitions

```python
# Missing concrete definitions for:
class ProcessingResult(BaseModel):
    # What fields exactly? File paths? Metadata? Processing time?
    # How does it integrate with different output formats?
    
class TranscriptSegment(BaseModel):
    # Timestamp format? Text content? Speaker identification?
    
class ProcessingMetadata(BaseModel):
    # Model versions? Cost estimates? Processing duration?
```

**Action Items**:
- [ ] Define complete `ProcessingResult` schema with all output paths and metadata
- [ ] Specify `TranscriptSegment` structure for merged transcript format
- [ ] Add `ProcessingMetadata` for tracking versions, costs, timing
- [ ] Define relationships between models and serialization formats

---

### **2. __meta: [Provider Registry Implementation]** - `providers/.../registry.py`
**Status**: 🔴 Critical Gap  
**Current**: References registry system but no implementation details  
**Needed**: Complete provider discovery and registration mechanism

**Action Items**:
- [ ] Define provider registration API and discovery mechanism
- [ ] Specify how providers are loaded dynamically at runtime
- [ ] Design provider validation and capability checking
- [ ] Document provider metadata format (models, descriptions, requirements)
- [ ] Define error handling for missing/invalid providers

**Key Questions**:
- How are providers discovered? Entry points? Directory scanning? Registry dict?
- What happens when a configured provider is unavailable?
- How do we validate provider capabilities (supported formats, models)?

---

### **3. __meta: [Exception Hierarchy]** - `core/exceptions.py`
**Status**: 🔴 Critical Gap  
**Current**: Placeholder mentioned but no concrete exception types  
**Needed**: Complete exception hierarchy for error handling

```python
# Missing exception definitions for:
class MinutiaError(Exception): ...
class ProviderError(MinutiaError): ...
class ConfigurationError(MinutiaError): ...
class FileProcessingError(MinutiaError): ...
class TranscriptionError(ProviderError): ...
class SummarizationError(ProviderError): ...
```

**Action Items**:
- [ ] Define base `MinutiaError` with common attributes
- [ ] Create provider-specific exceptions with context
- [ ] Add file processing errors for audio extraction failures
- [ ] Define configuration validation errors
- [ ] Specify error recovery strategies for each exception type

---

### **4. __meta: [Provider Configuration Type Safety]**
**Status**: 🟡 Architecture Issue  
**Current**: Generic `provider_config: Dict[str, Any]` lacks type safety  
**Needed**: Discriminated unions for type-safe provider configurations

**Current Problem**:
```python
class TranscriptionSettings(BaseSettings):
    provider: str = "whisper"
    provider_config: Dict[str, Any] = {}  # Not type-safe!
```

**Proposed Solution**:
```python
class WhisperConfig(BaseModel):
    device: str = "auto"
    compute_type: str = "float16"
    
class OpenAIConfig(BaseModel):
    api_key: str
    organization: Optional[str] = None

TranscriptionConfig = Union[WhisperConfig, OpenAIConfig]
```

**Action Items**:
- [ ] Define specific config models for each provider
- [ ] Implement discriminated unions based on provider field
- [ ] Add validation for provider-specific settings
- [ ] Update settings loading to handle typed configs

---

## Processing Logic Gaps

### **5. __meta: [Memory Management Strategy]**
**Status**: 🟡 Performance Issue  
**Current**: Assumes in-memory processing for all data  
**Needed**: Strategy for large files and streaming processing

**Action Items**:
- [ ] Define memory usage thresholds for streaming vs in-memory
- [ ] Design streaming interfaces for transcription providers
- [ ] Specify chunking strategies for large audio files
- [ ] Plan memory monitoring and cleanup procedures
- [ ] Document performance characteristics and limitations

**Key Decisions Needed**:
- At what file size do we switch to streaming?
- How do providers handle streaming vs batch processing?
- What's the memory footprint of different models?

---

### **6. __meta: [Pipeline Error Handling & Recovery]**
**Status**: 🟡 Robustness Issue  
**Current**: No failure mode handling or recovery strategies  
**Needed**: Comprehensive error handling and recovery mechanisms

**Action Items**:
- [ ] Define pipeline failure modes (network, disk, API limits)
- [ ] Design retry strategies with exponential backoff
- [ ] Specify partial failure handling (e.g., one audio track fails)
- [ ] Add progress persistence for long-running operations
- [ ] Design cleanup procedures for failed operations

**Scenarios to Handle**:
- API rate limiting or quota exhaustion
- Network timeouts during transcription/summarization
- Disk space issues during audio extraction
- Partial file corruption

---

### **7. __meta: [Cost Estimation & Monitoring]**
**Status**: 🟡 Feature Gap  
**Current**: Mentions cost estimation for Claude but not systematic  
**Needed**: Comprehensive cost tracking across all providers

**Action Items**:
- [ ] Define cost estimation interface for all providers
- [ ] Add pre-processing cost estimates and user confirmation
- [ ] Implement running cost tracking during processing
- [ ] Design cost reporting in results metadata
- [ ] Add cost budgeting and limiting features

---

## Configuration System Gaps

### **8. __meta: [Logging Configuration]**
**Status**: 🟡 Implementation Gap  
**Current**: Settings include `log_level`/`debug` but no format specification  
**Needed**: Complete logging setup with structured format

**Action Items**:
- [ ] Define structured logging format (JSON recommended)
- [ ] Specify log destinations (console, file, both)
- [ ] Design log rotation and retention policies
- [ ] Add provider-specific logging context
- [ ] Define debug vs production logging differences

---

### **9. __meta: [Environment Variable Mapping]**
**Status**: 🟡 Configuration Gap  
**Current**: Mentions `MINUTIA_` prefix but incomplete mapping  
**Needed**: Complete environment variable specification

**Action Items**:
- [ ] Document all supported environment variables
- [ ] Define nested setting access (e.g., `MINUTIA_AUDIO__MIC_TRACK`)
- [ ] Specify precedence order (CLI > env > .env > defaults)
- [ ] Add validation for environment variable formats
- [ ] Create example .env file template

---

## Testing & Quality Gaps

### **10. __meta: [Testing Strategy & Scope]**
**Status**: 🟡 Development Gap  
**Current**: Lists pytest/mypy but no concrete testing strategy  
**Needed**: Comprehensive testing plan with clear boundaries

**Action Items**:
- [ ] Define unit test scope and mocking strategy
- [ ] Plan integration tests for provider interactions
- [ ] Design CLI testing approach
- [ ] Specify test data requirements and fixtures
- [ ] Define performance/regression testing strategy

**Key Questions**:
- Do we mock all external API calls in unit tests?
- How do we test Rich UI components?
- What's our approach to testing file I/O operations?

---

## Documentation & Examples

### **11. __meta: [Usage Examples & Workflows]**
**Status**: 🟡 User Experience Gap  
**Current**: No concrete usage examples  
**Needed**: Complete user workflow documentation

**Action Items**:
- [ ] Create basic usage examples for common scenarios
- [ ] Document configuration file examples
- [ ] Add troubleshooting guide for common issues
- [ ] Create provider setup guides
- [ ] Document best practices for different use cases

---

## Implementation Priority Matrix

| Priority | Area | Impact | Effort | Status |
|----------|------|--------|--------|--------|
| 🔴 P0 | Data Models Schema | High | Medium | Not Started |
| 🔴 P0 | Provider Registry | High | High | Not Started |
| 🔴 P0 | Exception Hierarchy | High | Low | Not Started |
| 🟡 P1 | Provider Config Type Safety | Medium | Medium | Not Started |
| 🟡 P1 | Memory Management | Medium | High | Not Started |
| 🟡 P1 | Error Handling & Recovery | Medium | High | Not Started |
| 🟢 P2 | Cost Estimation | Low | Medium | Not Started |
| 🟢 P2 | Logging Configuration | Low | Low | Not Started |
| 🟢 P2 | Environment Variables | Low | Low | Not Started |
| 🟢 P2 | Testing Strategy | Low | High | Not Started |

## Next Steps for Design Iteration

1. **Immediate (P0)**: Expand data models, provider registry, and exception hierarchy
2. **Short-term (P1)**: Address type safety, memory management, and error handling
3. **Medium-term (P2)**: Complete configuration system and testing strategy
4. **Ongoing**: Update design document sections as each area is detailed

## Usage Instructions

When working on a specific aspect:
1. Choose an area from this TODO list
2. Review the current design document section
3. Expand that section with the missing details
4. Update this TODO with your progress
5. Cross-reference with planning document for consistency

This ensures incremental, focused improvements to reach an implementation-ready design.