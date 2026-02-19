import pytest
from pathlib import Path
import json

class FFmpegMock:
    """Simulates ffmpeg-python behavior for testing audio extraction."""
    
    def __init__(self):
        self.probes = {}
        self.calls = []
        self.output_files = []

    def set_probe_data(self, file_path: str | Path, audio_tracks: int = 3):
        """Register canned probe data for a file path."""
        path_str = str(file_path)
        streams = [{"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080}]
        for i in range(audio_tracks):
            streams.append({
                "index": i + 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "channels": 2
            })
        self.probes[path_str] = {"streams": streams}

    def probe(self, file_path: str):
        if file_path not in self.probes:
            # Default fallback for unregistered files
            self.set_probe_data(file_path)
        return self.probes[file_path]

    def run(self, output_node, capture_stdout=False, capture_stderr=False):
        """
        Simulates running the ffmpeg graph.
        In the real ffmpeg-python, the output_node contains the graph info.
        We'll just extract the output filename and create a dummy file.
        """
        # This is a bit of a hack because we aren't using the real graph.
        # In our extraction logic, the 'output_file' is passed to ffmpeg.output.
        # We need to find where that is stored in the mock node.
        self.calls.append(output_node)
        
        # If the output_node has a 'kwargs' or similar where we can find the filename
        # For simplicity in the mock, we might need to be clever or just assume 
        # the user passed something we can inspect.
        pass

@pytest.fixture
def dummy_wav():
    """Fixture to generate a dummy WAV file."""
    def _create(path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        # Minimal WAV header (44 bytes)
        header = (
            b"RIFF" + (36).to_bytes(4, "little") + b"WAVE" +
            b"fmt " + (16).to_bytes(4, "little") + b"\x01\x00" + b"\x01\x00" +
            (44100).to_bytes(4, "little") + (88200).to_bytes(4, "little") +
            (2).to_bytes(2, "little") + (16).to_bytes(2, "little") +
            b"data" + (0).to_bytes(4, "little")
        )
        path.write_bytes(header)
        return path
    return _create

from tests.mocks.chaos_config import chaos_config

@pytest.fixture
def mock_ffmpeg(mocker, dummy_wav, chaos_config):
    """
    Mock the ffmpeg module in the video_extraction step.
    This patches 'minutia.steps.video_extraction.ffmpeg'.
    """
    from minutia.steps import video_extraction
    
    mock_inst = FFmpegMock()
    
    def mock_probe(file_path):
        chaos_config.trigger_if_set("ffmpeg.probe")
        return mock_inst.probe(file_path)

    mocker.patch.object(video_extraction.ffmpeg, "probe", side_effect=mock_probe)
    
    # Mock input/output to return a mock node
    def mock_input(filename, **kwargs):
        chaos_config.trigger_if_set("ffmpeg.input")
        return mocker.MagicMock(name="InputNode", filename=filename)
    
    def mock_output(stream, filename, **kwargs):
        chaos_config.trigger_if_set("ffmpeg.output")
        node = mocker.Mock(name="OutputNode", filename=filename)
        return node

    def mock_run(node, **kwargs):
        chaos_config.trigger_if_set("ffmpeg.run")
        mock_inst.calls.append(node)
        # Create the actual file so downstream steps don't fail
        if hasattr(node, "filename"):
            dummy_wav(Path(node.filename))
        return (b"", b"")

    mocker.patch.object(video_extraction.ffmpeg, "input", side_effect=mock_input)
    mocker.patch.object(video_extraction.ffmpeg, "output", side_effect=mock_output)
    mocker.patch.object(video_extraction.ffmpeg, "run", side_effect=mock_run)
    
    return mock_inst
