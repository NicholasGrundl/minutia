# Minutia

Minutia processes OBS meeting recordings into searchable transcripts and
actionable summaries. The current refactor extracts the production notebook
workflow into a standalone Python module so the team can iterate toward the MVP
design in phases.

## Baseline Pipeline

Run the extracted pipeline directly with:

```bash
uv run python -m minutia.baseline_pipeline +recordings/2025-02-14_08-00-39-meetingnotes.mkv
```

Key behaviours preserved from the notebook:
- Audio extraction with deterministic output names inside dated run folders.
- Whisper transcription for microphone and desktop tracks.
- Transcript merge producing the existing JSON schema used by downstream tools.
- Cost estimation for Anthropic summarisation requests.
- Personal note injection and markdown snippets to inform the summary prompt.
- Optional Markdown export with an Anthropic-generated filename.
- ISO timestamped summaries when `--timestamp-summary` is set.

Use `minutia.baseline_pipeline --help` for the full list of options, including
prompt customisation, overlap parsing, and Markdown export toggles.

## Development

The project is managed with [`uv`](https://docs.astral.sh/uv/).

- Install dependencies: `uv sync --extra dev`
- Run formatting and linting: `make format` and `make lint`
- Execute the new smoke test: `uv run pytest tests/test_baseline_pipeline.py`

The implementation roadmap lives in `design/design.md` and `TASKS-TODO.md`.
Follow the phase order described there when extending the CLI.
