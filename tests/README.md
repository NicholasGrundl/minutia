# Minutia test suite

How the suite is laid out, what the fixtures do, and the exact setup sequence a
test goes through.

## Layout & tiers

```
tests/
├── conftest.py            # ROOT: env-scrub, plugin registration, auto-tiering, shared fixtures
├── mocks/                 # the four fixture-plugins (registered globally, opt-in per test)
│   ├── ffmpeg_mock.py     #   mock_ffmpeg, dummy_wav
│   ├── whisper_mock.py    #   mock_whisper
│   ├── llm_mock.py        #   mock_llm
│   └── chaos_config.py    #   chaos_config (error injection)
├── unit/                  # tier: unit          (mocks opt-in, no external services)
│   ├── conftest.py        #   sample_video_file / sample_run_paths
│   └── steps/
├── integration/           # tier: integration   (real ffmpeg/whisper, mocked Anthropic)
│   └── conftest.py        #   sample_* + sample_transcript_json / sample_legacy_transcript
├── slow/                  # tier: slow          (real Anthropic; skips without a real key)
│   └── conftest.py        #   _require_real_anthropic_key guard
├── fixtures/scenarios/    # golden-sample data (01_extracted → 04_summarized per scenario)
└── scripts/               # fixture-GENERATION tooling (excluded from the ty gate)
```

**Tier == directory.** There are no per-file `pytestmark` lines. The root
`pytest_collection_modifyitems` hook stamps `unit` / `integration` / `slow` onto
every test from its top-level directory. Put a file in the right folder and it is
tiered — that is the whole convention, and it is what kills marker drift.

Marker names are declared in `pyproject.toml [tool.pytest.ini_options]` with
`--strict-markers`, so a typo'd marker errors instead of silently passing. Import
mode is `importlib`; the `__init__.py` files are for packaging, not import magic.

## What fires for a single test — the setup sequence

For **every** test, in order:

1. **Collection** — pytest imports conftests and test modules, then
   `pytest_collection_modifyitems` runs once over all items and adds the tier
   marker per directory.
2. **`_scrub_minutia_environment`** (`tests/conftest.py`, `autouse=True`,
   function-scoped) — deletes every `MINUTIA_*`, `ANTHROPIC_API_KEY`, and
   `CLAUDE_API_KEY` from `os.environ` via `monkeypatch.delenv`. **This is the
   isolation root:** no test inherits your shell config, which is what eliminated
   the old full-suite ffmpeg hang. It runs before any lower-level fixture.
3. **Tier-specific autouse** (only in `slow/`) — `_require_real_anthropic_key`
   runs after the root scrub: it `skip`s the test unless a real `sk-ant-…` key was
   captured at import time, then re-injects that key past the scrub. Unit and
   integration have no autouse fixture beyond the root scrub.
4. **Requested fixtures resolve** — anything named in the test signature
   (`mock_ffmpeg`, `sample_run_paths`, `tmp_path`, …), deepest dependency first.
5. **Test body runs.**
6. **Teardown** — `monkeypatch` undoes env changes; `chaos_config` clears any
   injected failures; the `--timeout=60` in `addopts` aborts with a traceback if
   anything hangs.

Key point: **mocks are opt-in, not autouse.** A unit test gets a mock only if it
names it. A test that forgets to and reaches for a real service fails fast — no key
(scrubbed) and no ambient `RECORDINGS_DIR` — rather than hanging or spending money.
The env-scrub is the safety net; the mocks are the deliberate doubles.

## Fixture catalog

**Root (`tests/conftest.py`)** — available everywhere:
- `_scrub_minutia_environment` (autouse) — the isolation net above.
- `pytest_plugins = (chaos_config, ffmpeg_mock, llm_mock, whisper_mock)` —
  registers the four mock modules globally, which is why any tier can request
  `mock_ffmpeg` etc. (Replaced conftest re-imports that `ruff --fix` kept deleting.)
- `test_fixtures_dir` / `test_scenarios` (session-scoped) — locate and index
  `fixtures/scenarios/`.
- `scenario_loader` — load one named scenario's path + metadata.
- `run_paths_factory` / `pipeline_config_factory` — build `RunPaths` /
  `PipelineConfig` objects over `tmp_path`.

**`unit/conftest.py`** — `sample_video_file` (dummy `.mkv` in `tmp_path`),
`sample_run_paths`.

**`integration/conftest.py`** — the same, plus `sample_transcript_json`
(realistic mic+desktop JSON) and `sample_legacy_transcript` (bracketed-timestamp
format).

**`slow/conftest.py`** — only the real-key guard.

## The four mocks (all patch at the point of use)

| Fixture | Patches | Behavior |
|---|---|---|
| `mock_ffmpeg` | `video_extraction.ffmpeg` `.probe/.input/.output/.run` | Canned probe streams (1 video + N audio); `run` writes a real 44-byte WAV header so downstream steps find a file. Records `.calls`. |
| `mock_whisper` | `audio_transcription.whisper.load_model` + `torch.cuda.is_available → False` | `set_scenario(name, segments)` returns canned transcripts matched by audio filename; a default fallback otherwise. |
| `mock_llm` | `summarize_transcript.Anthropic` **and** `resolve_settings` in `config`/`cli`/`baseline_pipeline` | `set_responses([...])` pops replies in sequence, wrapped to mimic the SDK's `response.content[0].text` + `usage`. Also injects a fake `MinutiaSettings` so config resolution never touches disk/env. |
| `chaos_config` | (nothing directly) | Error injection. Every mock calls `chaos_config.trigger_if_set("<hook>")` at each seam; `set_failure(...)` / `set_error(...)` make that seam raise. This drives failure-path and partial-completion tests. |

Injectable seam names: `ffmpeg.probe/input/output/run`,
`whisper.load_model/transcribe`, `anthropic.init/messages.create`.

## Golden-sample scenarios

`fixtures/scenarios/<name>/` holds one real pipeline run frozen at each stage:

```
input.mkv → 01_extracted/ → 02_transcribed/ → 03_merged/ → 04_summarized/   (+ metadata.json)
```

Four scenarios: `microphone_only`, `noisy_microphone`, `podcast_desktop`,
`youtube_desktop`. The merge test (`integration/test_transcript_merger.py`) is the
pattern: feed `02_transcribed/` into the merger and assert the output reproduces
`03_merged/` on the stable metadata keys (`schema_version`, `parse_overlaps`,
`segment_count`, `total_duration`), ignoring fields that legitimately vary per run
(source paths, `processed_at` timestamps). Mocks built from real responses don't
lie. The scenarios are (re)generated by `tests/scripts/` — which is deliberately
outside the ruff/ty gate (fixture tooling + a notebook, optional-only deps).

## Per-tier contract

| Tier | ffmpeg | whisper | anthropic | key |
|---|---|---|---|---|
| `unit` | mock | mock | mock | scrubbed / fake |
| `integration` | real | real (tiny/base) | mock | scrubbed / fake |
| `slow` | real | real | **real** | **real, else the tier skips** |

## Running

```bash
just test-unit          # -m unit                    → fast loop
just test-integration   # -m "unit or integration"   → pre-commit validation
just test-all           # + slow                     → real API, needs an sk-ant- key
uv run pytest -k merge  # ad hoc; --timeout=60 is always on
just check-all          # full gate: ruff → ty → pytest
```

`ty` covers `src` + `tests` (excluding `tests/scripts/`); a small set of
type-inference diagnostics is baselined in `pyproject.toml [[tool.ty.overrides]]`
and tracked for tightening — see the ROADMAP "Known issues".
