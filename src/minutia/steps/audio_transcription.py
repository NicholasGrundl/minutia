import json
import os
from datetime import datetime, timezone

import whisper

from .logging import logger

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


def transcribe_audio(audio_path, model_name="base"):
    try:
        logger.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)

        logger.info(f"Transcribing audio file: {audio_path}")
        result = model.transcribe(audio_path)

        logger.info("Transcription completed successfully")
        return result
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
    mic_audio_path, desktop_audio_path, output_dir, whisper_model_name="base"
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
            transcription = transcribe_audio(audio_path, model_name=whisper_model_name)

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
