# Design Document Expansion Prompt Template

```
# State Info:

[TODO_SECTION_NAME]: __meta: [Data Models Schema] - data/models.py
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design complete data model schema for ProcessingResult, TranscriptSegment, and ProcessingMetadata with exact field definitions and serialization formats.

# Instructions

You are a senior software architect tasked with expanding and polishing the Minutia package design document. Your goal is to take a specific section from the design TODO and provide comprehensive, implementation-ready details.

## Context Files to Review
- **Current Design**: `@design/design.md` - The main design document
- **Design TODO**: `@design/design-todo.md` - Gap analysis and improvement areas
- **Planning Reference**: `@planning/planning-transcribe-and-summarize.md` - Original planning document

## Your Specific Task
Focus on: **[TODO_SECTION_NAME]** from the design TODO

[SPECIFIC_FOCUS_INSTRUCTIONS]

After thinking through your design update the relevant sections of @design/design.md to captgure the design for implemetation at a later date.

## Requirements

### 1. Implementation-Ready Detail
- Provide concrete code examples and schemas
- Include specific class definitions, method signatures, and data structures
- Show integration points with existing architecture
- Define clear interfaces and contracts

### 2. Consistency & Integration
- Ensure alignment with existing design patterns in `design.md`
- Reference and build upon the planning document architecture
- Maintain consistency with the package structure and naming conventions
- Consider impact on other system components

### 3. Documentation Quality
- Use clear, technical writing suitable for implementation teams
- Include code examples that demonstrate usage
- Provide rationale for design decisions
- Add implementation notes and considerations

### 4. Deliverables
[DELIVERABLE_REQUIREMENTS]

If no specific deliverables are provided above, analyze the TODO section and determine what implementation-ready artifacts are needed. This typically includes:
- Complete code/class definitions for any mentioned components
- Integration specifications with existing architecture
- Configuration or data structure definitions
- Error handling and validation approaches
- Testing considerations
- Usage examples demonstrating the implementation

## Output Format

### Section Title: [SECTION_NAME]

#### Current State Analysis
Brief summary of what's currently in the design document for this area.

#### Detailed Implementation Design
Comprehensive expansion with:
- Complete code examples
- Class/interface definitions
- Integration specifications
- Configuration details

#### Implementation Considerations
- Performance implications
- Error handling strategies
- Testing approaches
- Future extensibility

#### Integration Points
How this component integrates with:
- Configuration system
- Provider architecture
- Pipeline orchestration
- CLI interface

### Update Recommendations
Specific text additions/modifications for the design document, including:
- New sections to add
- Existing sections to modify
- Code examples to include

## Success Criteria
- The expanded section provides enough detail for a developer to implement without guessing
- All interfaces and contracts are clearly defined
- Integration with existing architecture is seamless
- The design maintains the package's modularity and extensibility goals

Focus on creating implementation-ready specifications that eliminate ambiguity and provide clear guidance for development teams.
```

---

# Quick Usage Examples

## Minimal Prompt (Auto-determines deliverables)
```
[TODO_SECTION_NAME]: __meta: [Data Models Schema] - data/models.py

[SPECIFIC_FOCUS_INSTRUCTIONS]:
Design the complete data model schema for ProcessingResult, TranscriptSegment, and ProcessingMetadata. Focus on exact field definitions, relationships between models, and integration with pipeline outputs.
```

## With Specific Deliverables
```
[TODO_SECTION_NAME]: __meta: [Provider Registry Implementation] - providers/.../registry.py

[SPECIFIC_FOCUS_INSTRUCTIONS]:
Design the complete provider discovery and registration system. Focus on dynamic provider loading, validation, and CLI integration for listing providers.

[DELIVERABLE_REQUIREMENTS]:
- Complete registry class implementation with entry points
- Provider metadata format and validation rules
- CLI command integration specifications
- Error handling for provider failures
```

## Ultra-Simple (Just the section)
```
[TODO_SECTION_NAME]: __meta: [Exception Hierarchy] - core/exceptions.py

[SPECIFIC_FOCUS_INSTRUCTIONS]:
Design the complete exception hierarchy for robust error handling throughout the application.
```

---

# All TODO Sections (Copy-Paste Ready)

## Critical Priority (P0)

### Data Models Schema
```
[TODO_SECTION_NAME]: __meta: [Data Models Schema] - data/models.py
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design complete data model schema for ProcessingResult, TranscriptSegment, and ProcessingMetadata with exact field definitions and serialization formats.
```

### Provider Registry
```
[TODO_SECTION_NAME]: __meta: [Provider Registry Implementation] - providers/.../registry.py
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design the complete provider discovery and registration system with dynamic loading and validation.
```

### Exception Hierarchy
```
[TODO_SECTION_NAME]: __meta: [Exception Hierarchy] - core/exceptions.py
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design complete exception hierarchy for robust error handling throughout pipelines and CLI.
```

## Important Priority (P1)

### Provider Configuration Type Safety
```
[TODO_SECTION_NAME]: __meta: [Provider Configuration Type Safety]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Replace generic Dict[str, Any] provider configs with type-safe discriminated unions using Pydantic.
```

### Memory Management Strategy
```
[TODO_SECTION_NAME]: __meta: [Memory Management Strategy]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design memory management strategy for large files including streaming interfaces and chunking algorithms.
```

### Pipeline Error Handling
```
[TODO_SECTION_NAME]: __meta: [Pipeline Error Handling & Recovery]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design comprehensive error handling and recovery mechanisms for pipeline failure modes.
```

## Nice-to-Have Priority (P2)

### Cost Estimation & Monitoring
```
[TODO_SECTION_NAME]: __meta: [Cost Estimation & Monitoring]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design systematic cost tracking across all providers with pre-processing estimates and budget controls.
```

### Logging Configuration
```
[TODO_SECTION_NAME]: __meta: [Logging Configuration]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design complete logging setup with structured format, destinations, and provider-specific context.
```

### Environment Variable Mapping
```
[TODO_SECTION_NAME]: __meta: [Environment Variable Mapping]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Complete environment variable specification with nested setting access and precedence rules.
```

### Testing Strategy
```
[TODO_SECTION_NAME]: __meta: [Testing Strategy & Scope]
[SPECIFIC_FOCUS_INSTRUCTIONS]: Design comprehensive testing plan with unit/integration boundaries and mocking strategies.
```

---

# Usage Instructions

1. **Pick a section** from the quick examples above
2. **Copy the prompt template** and fill in the placeholders
3. **Optionally add** specific deliverable requirements if you have particular needs
4. **Run with AI worker** or hand to junior developer
5. **Review and integrate** results into design.md
6. **Update TODO** to track progress

The prompt will automatically determine appropriate deliverables based on the TODO section if none are specified.