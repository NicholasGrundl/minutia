import os
from pathlib import Path

import panel as pn

# Enable the necessary extensions
pn.extension("fileinput", "audio", "widgets")


# Function to get a list of audio files from a directory
def get_audio_files(directory):
    audio_extensions = [".mp3", ".wav", ".ogg", ".flac"]
    return [
        f
        for f in os.listdir(directory)
        if any(f.endswith(ext) for ext in audio_extensions)
    ]


# Callback function to update the audio file list
def update_audio_list(event):
    audio_files = get_audio_files(event.new)
    audio_file_selector.options = audio_files
    if audio_files:
        audio_file_selector.value = audio_files[0]


# Callback function to update the audio player
def update_audio_player(event):
    audio_player.value = Path(directory_selector.value) / event.new


# Create the directory selector
directory_selector = pn.widgets.FileSelector(path=".", only_dirs=True)
directory_selector.observe(update_audio_list, names="value")

# Create the audio file selector
audio_file_selector = pn.widgets.Select(name="Audio Files")
audio_file_selector.observe(update_audio_player, names="value")

# Create the audio player
audio_player = pn.widgets.Audio(name="Audio Player")

# Layout the widgets
layout = pn.Column(
    pn.Row("Select a folder:", directory_selector),
    pn.Row("Select an audio file:", audio_file_selector),
    pn.Row(audio_player),
)
