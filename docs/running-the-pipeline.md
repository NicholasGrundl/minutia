# Running the pipeline on a new recording

This guide shows how to take a fresh OBS `.mkv` recording all the way to an
AI-generated meeting report. There are three ways to run it — pick based on how
much control you want.

> **Invocation note:** examples use `minutia`. If the console script isn't on your
> `PATH`, prefix every command with `uv run` (e.g. `uv run minutia`).

---

## Prerequisites

**Required**

- `ANTHROPIC_API_KEY` — needed for the summarization step.

  ```bash
  export ANTHROPIC_API_KEY=sk-ant-...
  ```

**Recommended environment** (all `MINUTIA_`-prefixed)

```bash
export MINUTIA_RECORDINGS_DIR=~/Videos        # where OBS drops .mkv files;
                                              # the wizard + `minutia run pipeline` browse it
export MINUTIA_OUTPUT_DIR=~/Documents/minutia # where artifacts are written
export MINUTIA_WHISPER_MODEL=medium.en        # transcription model (default: base)
```

> **Tip:** rather than exporting these by hand, run **`minutia setup`** once — it
> persists your recordings folder and API key to the user config for you.

**OBS audio tracks** — OBS records 1-indexed tracks; Minutia defaults to
**track 3 = microphone**, **track 2 = desktop**. Override per-run with
`--mic-track` / `--desktop-track`, or set `MINUTIA_MIC_TRACK` / `MINUTIA_DESKTOP_TRACK`.

**Check what's resolved** — this prints every config value and which layer supplied it:

```bash
minutia info                 # resolved settings + provenance
minutia info recordings      # list the newest .mkv files in the recordings folder
```

### Configuration layers

Minutia resolves settings in this order, with the leftmost value winning:

```text
CLI arguments > process environment > contextual .env > user config > built-in defaults
```

Durable personal defaults belong in
`platformdirs.user_config_path("minutia")/config.env` (`~/.config/minutia/config.env` on Linux).
Project-specific or temporary values—including API keys—belong in a contextual `.env` or the
process environment.

By default Minutia starts at the directory where it was invoked and loads the nearest `.env`,
stopping at the first `.git` or `pyproject.toml` project boundary and before the user's home
directory. It never chooses configuration based on the input recording or output directory.

```bash
minutia --env-file ./client.env info  # select an exact contextual file
minutia --no-env-file info            # use global config + process env only
```

Relative paths in an env-format file are resolved from that file's directory. Relative paths from
the process environment or CLI are resolved from the invocation directory.

---

## Recommended: step-by-step

Best for real use. Each step is **idempotent** — it skips work when its outputs
already exist (pass `--force` to redo a step). This matters because transcription
is slow and one-time, while summarization is the part you iterate (see below).

Each stage is a subcommand of `minutia run`:

```bash
# 1. Extract the two audio tracks from the MKV
minutia run extract-audio recording.mkv ./out/
#    -> ./out/microphone_audio.wav
#    -> ./out/desktop_audio.wav

# 2. Transcribe both tracks with Whisper
minutia run transcribe ./out/microphone_audio.wav ./out/desktop_audio.wav ./out/
#    -> ./out/microphone-whisper-medium.en_transcription.json
#    -> ./out/desktop-whisper-medium.en_transcription.json
#    (the model name is baked into the filename; it's `base` unless you set
#     MINUTIA_WHISPER_MODEL or pass --whisper-model)

# 3. Merge the two transcripts chronologically
minutia run merge \
    ./out/microphone-whisper-medium.en_transcription.json \
    ./out/desktop-whisper-medium.en_transcription.json \
    ./out/merged_transcript.json

# 4. Generate the AI-named markdown report (shows a cost estimate + confirm first)
minutia run summarize ./out/merged_transcript.json ./out/ --prompt-kind minutia
#    -> ./out/<AI-generated-name>.md
```

---

## Fastest: the guided wizard

Just run `minutia`. The bare command is a full-screen wizard that browses your
recordings folder, lets you pick the recording (with its date, size, and length)
and summary style, attach notes, and confirms the cost before spending anything —
then runs the whole pipeline with live progress.

```bash
minutia            # the wizard (first run walks setup, then guides each run)
```

If your recordings folder or API key aren't configured yet, the wizard runs
**setup** first (or run `minutia setup` on its own anytime).

---

## One-shot: whole pipeline in one line

Non-interactive; runs extract → transcribe → merge → summarize end to end. Good
for scripting. With `MINUTIA_RECORDINGS_DIR` set, the input is optional and the
newest `.mkv` is used.

```bash
minutia run pipeline recording.mkv ./out/
minutia run pipeline recording.mkv ./out/ --model claude-sonnet-4-6
minutia run pipeline --yes                    # newest recording, skip the cost prompt
```

---

## Iterating on summaries

The expensive, slow work (extract + transcribe + merge) only needs to happen
**once** per recording. Once you have a `merged_transcript.json`, re-run
`summarize` as many times as you like — different prompt flavors, notes, or
personal-info — without re-transcribing:

```bash
# Try a different summary flavor
minutia run summarize ./out/merged_transcript.json ./out/ --prompt-kind realtor

# Feed per-meeting notes / a speaker mapping, plus your personal-info file
minutia run summarize ./out/merged_transcript.json ./out/ \
    --prompt-kind minutia \
    --notes ./meeting-notes.md \
    --personal-info ./me.md

# See the token estimate + price WITHOUT calling the API
minutia run summarize ./out/merged_transcript.json ./out/ --dry-run

# Skip the cost confirmation prompt (for scripts)
minutia run summarize ./out/merged_transcript.json ./out/ --yes
```

**Available prompt kinds** (`--prompt-kind`): `minutia` (default), `baseline`,
`realtor`, `slide-review`, `interview-debrief`, `discovery-summary`.

**Choosing a model** (`--model`): `claude-opus-4-7`, `claude-opus-4-6`,
`claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-3-7-sonnet`,
`claude-3-haiku`. Defaults to the configured `MINUTIA_SUMMARY_MODEL`.
