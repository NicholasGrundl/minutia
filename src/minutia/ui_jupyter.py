# Audio Capture Widgets

import io
import threading

import ipywidgets as widgets
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
from IPython.display import display


class AudioCaptureWidget:
    def __init__(self, device_type='microphone'):
        self.device_type = device_type
        self.is_recording = False
        self.buffer = io.BytesIO()

        self.create_widgets()

    def create_widgets(self):
        self.start_button = widgets.Button(description=f"Start {self.device_type} Recording")
        self.stop_button = widgets.Button(description="Stop Recording", disabled=True)
        self.save_button = widgets.Button(description="Save Recording", disabled=True)
        self.status_label = widgets.Label(value="Ready")

        self.start_button.on_click(self.start_recording)
        self.stop_button.on_click(self.stop_recording)
        self.save_button.on_click(self.save_recording)

        self.widget = widgets.VBox([
            self.start_button,
            self.stop_button,
            self.save_button,
            self.status_label
        ])

    def start_recording(self, _):
        self.is_recording = True
        self.buffer = io.BytesIO()
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.save_button.disabled = True
        self.status_label.value = "Recording..."

        # Start recording in a separate thread
        threading.Thread(target=self._record).start()

    def _record(self):
        with sd.InputStream(callback=self._audio_callback, channels=2, samplerate=44100):
            while self.is_recording:
                sd.sleep(100)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.buffer.write(indata.tobytes())

    def stop_recording(self, _):
        self.is_recording = False
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.save_button.disabled = False
        self.status_label.value = "Recording stopped"

    def save_recording(self, _):
        audio_data = np.frombuffer(self.buffer.getvalue(), dtype=np.int16)
        audio_data = audio_data.reshape(-1, 2)
        wav.write(f"{self.device_type}_recording.wav", 44100, audio_data)
        self.status_label.value = f"Recording saved as {self.device_type}_recording.wav"

    def display(self):
        display(self.widget)

