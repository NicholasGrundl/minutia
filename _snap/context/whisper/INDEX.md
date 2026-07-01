# Whisper Context Index

This directory contains the full source code and technical reference for OpenAI's Whisper, a general-purpose speech recognition and translation model.

## 1. Documentation & Overview
- **[repo/README.md](./repo/README.md)**: Main entry point for setup, model sizes (tiny to large), CLI usage, and Python API examples.
- **[repo/model-card.md](./repo/model-card.md)**: Details on training data, intended use, and limitations.
- **[RESOURCES.md](./RESOURCES.md)**: Original source links and ingestion status.

## 2. Core Implementation (`repo/whisper/`)
- **[repo/whisper/transcribe.py](./repo/whisper/transcribe.py)**: The primary entry point for the `transcribe()` method and CLI implementation.
- **[repo/whisper/model.py](./repo/whisper/model.py)**: Defines the Transformer architecture and model dimensions.
- **[repo/whisper/audio.py](./repo/whisper/audio.py)**: Audio preprocessing, Mel-spectrogram generation, and padding/trimming logic.
- **[repo/whisper/tokenizer.py](./repo/whisper/tokenizer.py)**: Multilingual tokenizer implementation and language support list.
- **[repo/whisper/decoding.py](./repo/whisper/decoding.py)**: Low-level decoding logic and task-specific tokens (translate vs. transcribe).

## 3. Usage Patterns
- **CLI**: `whisper audio.mp3 --model turbo --language Japanese`
- **Python**: `model.transcribe("audio.mp3")` for high-level usage; see `repo/README.md` for low-level `decode()` patterns.
