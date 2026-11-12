# Minutia

Minutia turns OBS meeting recordings into searchable transcripts and actionable
summaries. It extracts per-track audio from an `.mkv`, transcribes each track
with Whisper, merges the transcripts chronologically, and generates an
AI-authored meeting report with Anthropic Claude.

The primary way to run it is the **`minutia` CLI**. A standalone
[`baseline_pipeline`](#baseline-pipeline-legacy-fallback) script remains as a
legacy fallback while the CLI reaches full parity.

## Install

Minutia is managed with [`uv`](https://docs.astral.sh/uv/) and requires
**Python `>=3.12,<3.14`** (Whisper's `torch` has no `cp314` wheels yet). It uses
the **anthropic 1.x** SDK.

The recommended way to run minutia is as a `uv` tool installed from the repo:

```bash
# Install the `minutia` command in its own isolated environment:
uv tool install git+https://github.com/NicholasGrundl/minutia@main
```

A recent uv selects a compatible interpreter automatically — no `--python` flag
needed. See **[docs/setup.md](docs/setup.md)** for the SSH alternative, upgrading,
the interpreter note, and developing from a local clone.

Set your API key before summarizing:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Quickstart

Just run `minutia`. The bare command is a full-screen **wizard** that
self-determines: the first time (before your recordings folder and API key are
set) it walks you through a one-time **setup**, then every run after that it's the
guided daily driver — pick a recording, choose a summary style, attach notes,
confirm the cost, and watch it run.

```bash
minutia            # the wizard — first run sets up, then guides each run
minutia setup      # re-run the config wizard (recordings folder + API key) anytime
minutia info       # show every resolved config value and where it came from
```

Setup persists your recordings folder and API key to the platform-specific
Minutia user config (`chmod 600`), so the tool is ready after first run. A
project-local `.env` is still discovered from the invocation directory; use
`minutia --env-file PATH ...` to select one or `minutia --no-env-file ...` to
disable contextual loading.

Prefer explicit, scriptable commands? Everything the wizard does is also available
under `minutia run` — the whole pipeline in one line (`minutia run pipeline`) or a
single stage at a time (`run extract-audio` → `transcribe` → `merge` →
`summarize`). See **[docs/running-the-pipeline.md](docs/running-the-pipeline.md)**
for the full walkthrough.

## Development

The project uses `uv` for packages and [`just`](https://github.com/casey/just)
as the task runner. Common recipes:

```bash
just sync          # install/sync the dev environment
just lint          # ruff check (read-only)
just format        # ruff format
just ty            # type-check
just check-all     # dev gate: mutating ruff, then ty, then the test suite
just test          # run the test suite (forwards args, e.g. `just test -k merge`)
```

Run `just` with no arguments to list every recipe.

## Baseline Pipeline (legacy fallback)

Before the CLI orchestrator existed, the extracted notebook workflow ran as a
single script. It still works and is kept as a fallback until the CLI reaches
parity:

```bash
uv run python -m minutia.baseline_pipeline +recordings/2025-02-14_08-00-39-meetingnotes.mkv
```

Behaviours preserved from the notebook:
- Audio extraction with deterministic output names inside dated run folders.
- Whisper transcription for microphone and desktop tracks.
- Transcript merge producing the JSON schema used by downstream tools.
- Cost estimation for Anthropic summarisation requests.
- Personal note injection and markdown snippets to inform the summary prompt.
- Optional Markdown export with an Anthropic-generated filename.
- ISO timestamped summaries when `--timestamp-summary` is set.

Use `minutia.baseline_pipeline --help` for the full option list, including
prompt customisation, overlap parsing, and Markdown export toggles.
