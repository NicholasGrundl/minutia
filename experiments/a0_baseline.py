#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai-whisper",
#     "loguru",
# ]
# ///
"""
A0 — Baseline Whisper transcription.

Runs `whisper medium.en` (or any model passed via --model) on a single WAV
file and writes a JSON transcript matching the project's schema. This is the
reference point every other experiment compares against.

Run from project root:
    uv run experiments/a0_baseline.py +outputs/audio_track_1.wav
    uv run experiments/a0_baseline.py +outputs/audio_track_1.wav --model large-v3
    uv run experiments/a0_baseline.py +outputs/audio_track_1.wav --cpu
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import whisper
from loguru import logger

TRANSCRIPT_SCHEMA_VERSION = "1.0"


def normalise_segment(segment: dict) -> dict:
    """Convert a Whisper segment dict into the project's JSON schema."""
    serialised = {
        "id": segment.get("id"),
        "start_time": float(segment["start"]),
        "end_time": float(segment["end"]),
        "text": segment.get("text", "").strip(),
        "tokens": segment.get("tokens"),
        "temperature": segment.get("temperature"),
        "avg_logprob": segment.get("avg_logprob"),
        "compression_ratio": segment.get("compression_ratio"),
        "no_speech_prob": segment.get("no_speech_prob"),
    }
    return {k: v for k, v in serialised.items() if v is not None}


def run(audio_path: Path, output_dir: Path, model_name: str, use_gpu: bool) -> Path:
    device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"
    if use_gpu and device == "cpu":
        logger.warning("GPU requested but CUDA unavailable — falling back to CPU.")

    if device == "cuda":
        logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB)")
        torch.cuda.empty_cache()
    else:
        logger.info("Running on CPU.")

    logger.info(f"Loading Whisper model: {model_name} on {device}")
    model = whisper.load_model(model_name, device=device)
    n_params = sum(p.numel() for p in model.parameters()) / 1e6
    logger.info(f"Model loaded: {n_params:.0f}M parameters")

    logger.info(f"Transcribing: {audio_path}")
    t0 = time.time()
    result = model.transcribe(
        str(audio_path),
        fp16=(device == "cuda"),
        verbose=False,
    )
    elapsed = time.time() - t0
    duration = result.get("duration", 0.0)

    if duration:
        logger.info(f"Done in {elapsed:.1f}s ({duration:.1f}s audio → {duration / elapsed:.1f}× realtime)")
    else:
        logger.info(f"Done in {elapsed:.1f}s")

    if device == "cuda":
        logger.info(f"Peak GPU memory: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")

    output_path = output_dir / f"master-whisper-{model_name}_a0-baseline_transcription.json"
    transcript = {
        "metadata": {
            "experiment": "A0_baseline",
            "source_file": str(audio_path),
            "model": model_name,
            "language": result.get("language"),
            "duration": result.get("duration"),
            "task": result.get("task"),
            "device": device,
            "elapsed_s": round(elapsed, 2),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": TRANSCRIPT_SCHEMA_VERSION,
        },
        "segments": [normalise_segment(s) for s in result["segments"]],
        "text": result.get("text", "").strip(),
    }
    transcript["metadata"] = {k: v for k, v in transcript["metadata"].items() if v is not None}

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="A0 baseline Whisper transcription.")
    parser.add_argument("audio", type=Path, help="Path to a WAV/MP3/etc. audio file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("+outputs"),
        help="Directory to write the JSON transcript (default: +outputs/).",
    )
    parser.add_argument(
        "--model",
        default="medium.en",
        help="Whisper model name (default: medium.en). Try: tiny.en, base.en, small.en, medium.en, large-v3.",
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even if CUDA is available.")
    args = parser.parse_args()

    if not args.audio.exists():
        logger.error(f"Audio file not found: {args.audio}")
        return 1

    run(
        audio_path=args.audio,
        output_dir=args.output_dir,
        model_name=args.model,
        use_gpu=not args.cpu,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
