import io

import panel as pn
import param

pn.extension()

class AudioSelectionWidget(param.Parameterized):
    file_input = param.Parameter()
    audio_player = param.Parameter()
    audio_info = param.String("No file selected")

    def __init__(self, **params):
        super().__init__(**params)
        self.file_input = pn.widgets.FileInput(accept='.wav')
        self.audio_player = pn.widgets.Audio(name='Audio Player', sizing_mode='stretch_width')
        self.play_button = pn.widgets.Button(name='Play', button_type='primary', disabled=True)

        self.file_input.param.watch(self.update_audio, 'value')
        self.play_button.on_click(self.play_audio)

    def update_audio(self, event):
        print("File selected, updating audio...")  # Debug print
        if event.new:
            filename = self.file_input.filename
            print(f"File name: {filename}")  # Debug print

            # Create a BytesIO object from the uploaded file content
            audio_data = io.BytesIO(event.new)

            # Update the audio player with the new file
            self.audio_player.object = audio_data
            self.audio_player.name = filename
            self.play_button.disabled = False

            # Update audio info
            self.audio_info = f"Selected: {filename}"
            print(f"Audio info updated: {self.audio_info}")  # Debug print
        else:
            print("No file content received")  # Debug print

    def play_audio(self, event):
        if self.audio_player.object:
            print("Playing audio...")  # Debug print
            self.audio_player.playing = True

    @param.depends('audio_info')
    def get_audio_info(self):
        return self.audio_info

    @pn.depends('file_input.value', 'audio_info')
    def panel(self):
        return pn.Column(
            self.file_input,
            pn.pane.Markdown(self.get_audio_info),
            self.play_button,
            self.audio_player
        )




