from pathlib import Path

import pytest


class WhisperMock:
    """Simulates OpenAI Whisper model behavior for testing."""

    def __init__(self):
        self.scenarios = {}  # audio_path_name -> result_dict
        self.calls = []

    def set_scenario(self, audio_name: str, segments: list[dict], text: str = ""):
        """
        Register a canned response for a given audio identifier.
        audio_name is matched against the filename of the audio_path.
        """
        if not text and segments:
            text = " ".join([s.get("text", "") for s in segments])

        self.scenarios[audio_name] = {
            "text": text,
            "segments": segments,
            "language": "en",
            "duration": segments[-1]["end"] if segments else 0.0,
            "task": "transcribe",
        }

    def transcribe(self, audio_path, **kwargs):
        path = Path(audio_path)
        self.calls.append({"path": str(path), "kwargs": kwargs})

        # Match by filename stem or full name
        result = self.scenarios.get(path.name) or self.scenarios.get(path.stem)

        if result:
            return result

        # Default fallback
        return {
            "text": "This is a default mocked transcription.",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "This is a default mocked transcription.",
                }
            ],
            "language": "en",
            "duration": 2.0,
        }


@pytest.fixture
def mock_whisper(mocker, chaos_config):
    """
    Mock the whisper module and torch.cuda in audio_transcription.
    """
    from minutia.steps import audio_transcription

    mock_inst = WhisperMock()

    def mock_transcribe(audio_path, **kwargs):
        chaos_config.trigger_if_set("whisper.transcribe")
        return mock_inst.transcribe(audio_path, **kwargs)

    # Mock whisper.load_model
    def mock_load_model(model_name, device=None):
        chaos_config.trigger_if_set("whisper.load_model")
        mock_model = mocker.Mock()
        mock_model.transcribe.side_effect = mock_transcribe
        mock_model.parameters.return_value = [mocker.Mock(numel=lambda: 1000000)]
        return mock_model

    mocker.patch.object(
        audio_transcription.whisper, "load_model", side_effect=mock_load_model
    )

    # Mock torch.cuda.is_available to avoid needing a GPU in tests by default
    mocker.patch.object(
        audio_transcription.torch.cuda, "is_available", return_value=False
    )

    return mock_inst
