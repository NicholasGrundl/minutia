import whisper
import torch
import sys
import logging
import os

def setup_logger(name="whisper", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

# Usage
logger = setup_logger()

def transcribe_audio(audio_path, model_name="base"):
    try:
        logger.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)

        logger.info(f"Transcribing audio file: {audio_path}")
        result = model.transcribe(audio_path)

        logger.info("Transcription completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise

def save_transcription(transcription, output_path):
    try:
        logger.info(f"Saving transcription to: {output_path}")
        with open(output_path, "w") as f:
            for segment in transcription["segments"]:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
        logger.info("Transcription saved successfully")
    except Exception as e:
        logger.error(f"Error saving transcription: {str(e)}")
        raise

def process_audio_files(mic_audio_path, desktop_audio_path, output_dir, whisper_model_name='base'):
    try:
        os.makedirs(output_dir, exist_ok=True)
        filenames = {}
        for audio_type, audio_path in [("microphone", mic_audio_path), ("desktop", desktop_audio_path)]:
            if not os.path.exists(audio_path):
                logger.error(f"{audio_type.capitalize()} audio file not found: {audio_path}")
                continue

            logger.info(f"Processing {audio_type} audio")
            transcription = transcribe_audio(audio_path, model_name=whisper_model_name)
            
            output_path = os.path.join(output_dir, f"{audio_type}-whisper-{whisper_model_name}_transcription.txt")
            save_transcription(transcription, output_path)
            filenames[audio_type] = output_path
        logger.info("Audio processing completed")
        return filenames
    except Exception as e:
        logger.error(f"Error processing audio files: {str(e)}")
        raise