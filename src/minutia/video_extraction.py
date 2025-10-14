# Import necessary libraries
import logging
import os
import re
import shutil
import sys

import ffmpeg

# Optional imports removed - they were not being used in the code


# Set up logger
def setup_ffmpeg_logger():
    logger = logging.getLogger('ffmpeg')
    logger.propagate = False  # Turn off propagation
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

logger = setup_ffmpeg_logger()


# Helper functions
def get_video_info(file_path):
    """
    Get information about the video file.
    """
    probe = ffmpeg.probe(file_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    return video_info, audio_streams

def extract_audio_track(input_file, output_file, track_index=0):
    """
    Extract a specific audio track from the video file.
    """
    input_stream = ffmpeg.input(input_file)
    audio = input_stream['a:' + str(track_index)]
    output = ffmpeg.output(audio, output_file)
    ffmpeg.run(output, capture_stdout=False, capture_stderr=True)

def list_files_in_directory(directory):
    """
    List all files in a given directory.
    """
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def extract_all_audio_tracks(input_file, output_directory):
    """
    Extract all audio tracks from the input .mkv file and save them as separate files.
    """
    # Get video information
    _, audio_streams = get_video_info(input_file)

    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Extract each audio track
    extracted_files = []
    for i, _ in enumerate(audio_streams):
        output_file = os.path.join(output_directory, f"audio_track_{i+1}.wav")
        extract_audio_track(input_file, output_file, i)
        extracted_files.append(output_file)

    return extracted_files

def identify_audio_tracks(audio_files, mic_track_number=3, desktop_track_number=2):
    """
    Identify which audio file corresponds to the microphone and desktop audio
    based on the provided track numbers. OBS uses 1 index tracks.

    :param audio_files: List of audio file paths
    :param mic_track_number: The track number corresponding to the microphone audio
    :param desktop_track_number: The track number corresponding to the desktop audio
    :return: Dictionary with 'microphone' and 'desktop' keys and corresponding file paths
    """
    logger.info("Identifying audio tracks based on provided track numbers")

    mic_file = None
    desktop_file = None

    track_pattern = re.compile(r'track_(\d+)$')

    for file in audio_files:
        filename = os.path.splitext(os.path.basename(file))[0]  # Get filename without extension
        match = track_pattern.search(filename)

        if match:
            track_number = int(match.group(1))

            if track_number == mic_track_number:
                mic_file = file
                logger.info(f"Identified microphone audio: {mic_file}")
            elif track_number == desktop_track_number:
                desktop_file = file
                logger.info(f"Identified desktop audio: {desktop_file}")

    if not mic_file:
        logger.error(f"Could not find microphone audio file with track number {mic_track_number}")
    if not desktop_file:
        logger.error(f"Could not find desktop audio file with track number {desktop_track_number}")

    if not mic_file or not desktop_file:
        raise ValueError("Could not identify both microphone and desktop audio files.")

    return {
        "microphone": mic_file,
        "desktop": desktop_file
    }

def copy_and_rename_audio_files(identified_tracks, output_directory):
    """
    Create copies of the identified audio files with descriptive names.
    """
    renamed_tracks = {}
    for track_type, file_path in identified_tracks.items():
        new_file_name = f"{track_type}_audio.wav"
        new_file_path = os.path.join(output_directory, new_file_name)
        shutil.copy2(file_path, new_file_path)
        renamed_tracks[track_type] = new_file_path
    return renamed_tracks


def process_mkv_file(input_mkv, output_dir):
    """
    Process an .mkv file to extract and identify audio tracks.
    """
    logger.info(f"Processing file: {input_mkv}")

    # Extract all audio tracks
    extracted_files = extract_all_audio_tracks(input_mkv, output_dir)
    logger.info(f"Extracted {len(extracted_files)} audio tracks")

    # Identify microphone and desktop audio
    identified_tracks = identify_audio_tracks(audio_files=extracted_files)

    # Create copies with descriptive names
    renamed_tracks = copy_and_rename_audio_files(identified_tracks, output_dir)

    logger.info("Audio track separation completed:")
    logger.info(f"Microphone audio saved as: {renamed_tracks['microphone']}")
    logger.info(f"Desktop audio saved as: {renamed_tracks['desktop']}")

    return renamed_tracks
