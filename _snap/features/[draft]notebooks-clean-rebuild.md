---
state: draft
changelog:
  "2026-09-08": "Initial stub — new spec called for by EXECUTIVE_SUMMARY.md §6. First feature
    branch off the new main per §7."
---

# notebooks-clean-rebuild (parked)

## Executive Overview

Rebuild `notebooks/` from scratch, clean this time (EXECUTIVE_SUMMARY.md §6). The old notebooks
carried real-meeting PII, mixed dev/experiment/production concerns, committed cell outputs, and
quietly became the daily driver — they're now out of git history, salvage-only in `+notebooks/`.

**Target policy for the new notebooks:**
- Synthetic / public data only — reuse `tests/fixtures/scenarios/` golden samples as demo inputs;
  never a real recording or transcript.
- Outputs cleared on commit (`nbstripout` or equivalent); `.ipynb_checkpoints/` stays gitignored.
- Thin over the package — notebooks *demonstrate* `minutia.steps.*` / `minutia.prompts` / the
  CLI; they never re-implement pipeline logic.
- A small purposeful set, e.g. `01_quickstart_demo`, `02_prompt_kinds_tour`,
  `03_transcription_experiments` (the eval sandbox).

**Parked** — scoped placeholder. Per §7 this is the first feature branch cut off the new `main`
(fast; unblocks daily use + demos). Expand into a full task checklist in its own PLAN/BUILD
session then.

## Details

Salvage from `+notebooks/` and `+planning/transcription_experiments.md` (Whisper arg tuning,
faster-whisper/WhisperX/pyannote scaffolds) into `03_…`, rewritten against synthetic audio.
