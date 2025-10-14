import os

import whisper
from .logging import logger


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


def save_transcription(transcription, output_path):
    try:
        logger.info("Saving transcription to: {}", output_path)
        with open(output_path, "w") as f:
            for segment in transcription["segments"]:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
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
                f"{audio_type}-whisper-{whisper_model_name}_transcription.txt",
            )
            save_transcription(transcription, output_path)
            filenames[audio_type] = output_path
        logger.info("Audio processing completed")
        return filenames
    except Exception as e:
        logger.exception("Error processing audio files: {}", e)
        raise
