import json
import os
import time
from datetime import datetime, timezone

import torch
import whisper

from ..logging import logger

TRANSCRIPT_SCHEMA_VERSION = "1.0"


def _normalise_segment(segment):
    """Convert Whisper segment metadata into the project JSON schema."""
    start = float(segment["start"])
    end = float(segment["end"])
    text = segment.get("text", "").strip()
    serialised = {
        "id": segment.get("id"),
        "start_time": start,
        "end_time": end,
        "text": text,
        "tokens": segment.get("tokens"),
        "temperature": segment.get("temperature"),
        "avg_logprob": segment.get("avg_logprob"),
        "compression_ratio": segment.get("compression_ratio"),
        "no_speech_prob": segment.get("no_speech_prob"),
    }
    return {key: value for key, value in serialised.items() if value is not None}


def transcribe_audio(audio_path, model_name="base", use_gpu=True):
    """
    Transcribe audio using Whisper with optional GPU acceleration.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model to use ("tiny", "base", "small", "medium", "large")
        use_gpu: Whether to use GPU acceleration if available
    """
    try:
        # Determine device
        if use_gpu and torch.cuda.is_available():
            device = "cuda"
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            torch.cuda.empty_cache()
        else:
            device = "cpu"
            logger.info("Using CPU for transcription")
            if use_gpu and not torch.cuda.is_available():
                logger.warning("GPU requested but CUDA is not available, falling back to CPU")
        
        logger.info(f"Loading Whisper model: {model_name} on {device}")
        model = whisper.load_model(model_name, device=device)
        
        # Log model info
        model_params = sum(p.numel() for p in model.parameters()) / 1e6
        logger.info(f"Model loaded: {model_params:.0f}M parameters")
        
        logger.info(f"Transcribing audio file: {audio_path}")
        
        # Start timing
        start_time = time.time()
        
        # Transcribe with GPU optimization
        result = model.transcribe(
            audio_path,
            fp16=(device == "cuda"),  # Use FP16 on GPU for faster processing
            verbose=False  # Disable whisper's verbose output to use our logger
        )
        
        # Calculate processing metrics
        elapsed_time = time.time() - start_time
        audio_duration = result.get("duration", 0)
        
        if audio_duration > 0:
            speed_ratio = audio_duration / elapsed_time
            logger.info(f"Transcription completed in {elapsed_time:.1f}s")
            logger.info(f"Audio duration: {audio_duration:.1f}s")
            logger.info(f"Processing speed: {speed_ratio:.2f}x realtime")
        else:
            logger.info(f"Transcription completed in {elapsed_time:.1f}s")
        
        # Log GPU memory usage if using CUDA
        if device == "cuda":
            memory_used = torch.cuda.max_memory_allocated() / 1e9
            logger.info(f"Peak GPU memory used: {memory_used:.2f} GB")
            torch.cuda.empty_cache()
        
        return result
        
    except torch.cuda.OutOfMemoryError:
        logger.error("GPU out of memory! Try a smaller model")
        raise
    except Exception as e:
        logger.exception("Error during transcription: {}", e)
        raise

def save_transcription(transcription, output_path, source_audio, model_name):
    try:
        logger.info("Saving transcription to: {}", output_path)
        segments = [_normalise_segment(segment) for segment in transcription["segments"]]
        transcript_json = {
            "metadata": {
                "source_file": source_audio,
                "model": model_name,
                "language": transcription.get("language"),
                "duration": transcription.get("duration"),
                "task": transcription.get("task"),
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": TRANSCRIPT_SCHEMA_VERSION,
            },
            "segments": segments,
            "text": transcription.get("text", "").strip(),
        }
        transcript_json["metadata"] = {
            key: value for key, value in transcript_json["metadata"].items() if value is not None
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {key: value for key, value in transcript_json.items() if value is not None},
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info("Transcription saved successfully")
    except Exception as e:
        logger.exception("Error saving transcription: {}", e)
        raise


def process_audio_files(
    mic_audio_path, desktop_audio_path, output_dir, whisper_model_name="base", use_gpu=True
):
    try:
        os.makedirs(output_dir, exist_ok=True)
        filenames = {}
        for audio_type, audio_path in [
            ("microphone", mic_audio_path),
            ("desktop", desktop_audio_path),
        ]:
            if not os.path.exists(audio_path):
                logger.error(
                    "{} audio file not found: {}", audio_type.capitalize(), audio_path
                )
                continue

            logger.info("Processing {} audio", audio_type)
            transcription = transcribe_audio(audio_path, model_name=whisper_model_name, use_gpu=use_gpu)

            output_path = os.path.join(
                output_dir,
                f"{audio_type}-whisper-{whisper_model_name}_transcription.json",
            )
            save_transcription(
                transcription,
                output_path,
                source_audio=audio_path,
                model_name=whisper_model_name,
            )
            filenames[audio_type] = output_path
        logger.info("Audio processing completed")
        return filenames
    except Exception as e:
        logger.exception("Error processing audio files: {}", e)
        raise
