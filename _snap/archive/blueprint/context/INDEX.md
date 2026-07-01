# Technical Context Master Index

This directory serves as the centralized knowledge base for the project. It contains curated technical references, implementation patterns, and specialized documentation for the core tools and frameworks in our stack.

## 1. Agentic Frameworks & Skills
Expertise for building, extending, and automating AI agents.
- **[agent-skills/](./agent-skills/INDEX.md)**: Technical specifications for the open "Agent Skills" format.
- **[claude/](./claude/INDEX.md)**: Specialized guide for building and deploying skills in the Claude ecosystem.
- **[gemini-cli/](./gemini-cli/INDEX.md)**: Reference for configuring and automating the Gemini CLI (hooks, custom commands, sub-agents).

## 2. Testing Ecosystem
Comprehensive patterns for robust, data-driven, and isolated testing.
- **[pytest/](./pytest/INDEX.md)**: The "Pytest Pyramid" — covers everything from basic assertions to advanced fixture architecture.
- **[pytest-mock/](./pytest-mock/INDEX.md)**: Deep dive into the `mocker` fixture, including spying, stubbing, and async mocks.

## 3. Media Processing
Context for audio/video transcription, analysis, and transformation pipelines.
- **[whisper/](./whisper/INDEX.md)**: Source-level reference for OpenAI's Whisper model and API.
- **[ffmpeg/](./ffmpeg/INDEX.md)**: Synthesized CLI reference for `ffmpeg`, `ffprobe`, and filtergraph syntax.

## 4. Core Python Tooling
Static analysis, cross-platform utilities, and fast string processing.
- **[ruff/](./ruff/INDEX.md)**: High-speed linting and formatting configuration.
- **[ty/](./ty/INDEX.md)**: `ty` (Rust-powered) type checking reference.
- **[platformdirs/](./platformdirs/INDEX.md)**: Cross-platform directory access (cache, config, data).
- **[rapidfuzz/](./rapidfuzz/INDEX.md)**: Fast string matching and fuzzy comparison.

---

**Note to Agents**: Always start by reading the `INDEX.md` within a specific subdirectory to locate the exact procedural or architectural knowledge you need.
