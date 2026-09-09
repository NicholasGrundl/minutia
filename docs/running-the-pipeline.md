# Running the pipeline on a new recording

This guide shows how to take a fresh OBS `.mkv` recording all the way to an
AI-generated meeting report. There are three ways to run it — pick based on how
much control you want.

> **Invocation note:** examples use `minutia`. If the console script isn't on your
> `PATH`, prefix every command with `uv run` (e.g. `uv run minutia go`).

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
                                              # enables bare `minutia go` / `process-all`
export MINUTIA_OUTPUT_DIR=~/Documents/minutia # where artifacts are written
export MINUTIA_WHISPER_MODEL=medium.en        # transcription model (default: base)
```

**OBS audio tracks** — OBS records 1-indexed tracks; Minutia defaults to
**track 3 = microphone**, **track 2 = desktop**. Override per-run with
`--mic-track` / `--desktop-track`, or set `MINUTIA_MIC_TRACK` / `MINUTIA_DESKTOP_TRACK`.

**Check what's resolved** — this prints every config value and which layer supplied it:

```bash
minutia config
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
minutia --env-file ./client.env config  # select an exact contextual file
minutia --no-env-file config            # use global config + process env only
```

Relative paths in an env-format file are resolved from that file's directory. Relative paths from
the process environment or CLI are resolved from the invocation directory.

---

## Recommended: step-by-step

Best for real use. Each step is **idempotent** — it skips work when its outputs
already exist (pass `--force` to redo a step). This matters because transcription
is slow and one-time, while summarization is the part you iterate (see below).

```bash
# 1. Extract the two audio tracks from the MKV
minutia extract-audio recording.mkv ./out/
#    -> ./out/microphone_audio.wav
#    -> ./out/desktop_audio.wav

# 2. Transcribe both tracks with Whisper
minutia transcribe ./out/microphone_audio.wav ./out/desktop_audio.wav ./out/
#    -> ./out/microphone-whisper-medium.en_transcription.json
#    -> ./out/desktop-whisper-medium.en_transcription.json
#    (the model name is baked into the filename; it's `base` unless you set
#     MINUTIA_WHISPER_MODEL or pass --whisper-model)

# 3. Merge the two transcripts chronologically
minutia merge-transcripts \
    ./out/microphone-whisper-medium.en_transcription.json \
    ./out/desktop-whisper-medium.en_transcription.json \
    ./out/merged_transcript.json

# 4. Generate the AI-named markdown report (shows a cost estimate + confirm first)
minutia summarize ./out/merged_transcript.json ./out/ --prompt-kind minutia
#    -> ./out/<AI-generated-name>.md
```

---

## Fastest: guided run

One interactive command. It browses your recordings directory, lets you pick the
recording and prompt kind, and confirms the cost before spending anything.

```bash
minutia go                # browses MINUTIA_RECORDINGS_DIR
minutia go ./some/dir     # browse a specific directory instead
```

---

## One-shot: whole pipeline in one line

Non-interactive; runs extract → transcribe → merge → summarize end to end. Good
for scripting. With `MINUTIA_RECORDINGS_DIR` set, the input is optional and the
newest `.mkv` is used.

```bash
minutia process-all recording.mkv ./out/
minutia process-all recording.mkv ./out/ --model claude-sonnet-4-6
minutia process-all                        # newest recording, default output dir
```

---

## Iterating on summaries

The expensive, slow work (extract + transcribe + merge) only needs to happen
**once** per recording. Once you have a `merged_transcript.json`, re-run
`summarize` as many times as you like — different prompt flavors, notes, or
personal-info — without re-transcribing:

```bash
# Try a different summary flavor
minutia summarize ./out/merged_transcript.json ./out/ --prompt-kind realtor

# Feed per-meeting notes / a speaker mapping, plus your personal-info file
minutia summarize ./out/merged_transcript.json ./out/ \
    --prompt-kind minutia \
    --notes ./meeting-notes.md \
    --personal-info ./me.md

# See the token estimate + price WITHOUT calling the API
minutia summarize ./out/merged_transcript.json ./out/ --dry-run

# Skip the cost confirmation prompt (for scripts)
minutia summarize ./out/merged_transcript.json ./out/ --yes
```

**Available prompt kinds** (`--prompt-kind`): `minutia` (default), `baseline`,
`realtor`, `slide-review`, `interview-debrief`, `discovery-summary`.

**Choosing a model** (`--model`): `claude-opus-4-7`, `claude-opus-4-6`,
`claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-3-7-sonnet`,
`claude-3-haiku`. Defaults to the configured `MINUTIA_SUMMARY_MODEL`.
