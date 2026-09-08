---
state: ready
changelog:
  "2026-09-08": "Extracted from [active]refactor_to_cli Phase 4 milestone during the §5
    spec-split (EXECUTIVE_SUMMARY.md). The live milestone that lets refactor_to_cli close."
---

# finish-cli-parity — the live milestone + notebook retirement

## Executive Overview

The last unfinished piece of `refactor_to_cli`: prove the CLI at parity with the notebook by
running **one real meeting end-to-end, CLI-only**, then retire the notebook as the daily driver.
Everything short of a live Whisper + Anthropic run is already verified against golden-sample
fixtures; this is the human-in-the-loop confirmation on real audio.

Once this passes, `refactor_to_cli` can be marked `[done]` (Phases 0–4 code complete + validated).

**Non-goals:** no new code expected (bugfixes only if the real run surfaces them); eval seams and
orchestrator/baseline retirement are their own specs.

## Task Checklist

- [ ] Run one real meeting end-to-end using only CLI commands — either the step sequence
      (`extract-audio` → `transcribe` → `merge-transcripts` → `summarize`) or `minutia go`.
- [ ] Confirm the output matches notebook expectations (transcript quality, merge ordering,
      summary shape, AI-named markdown report).
- [ ] Retire the notebook for daily use (stop driving work from it); log the retirement in
      `_snap/DECISIONS.md`.
- [ ] Flip `refactor_to_cli` → `[done]` (its own `git mv`/rename step).

## Details

Source: `_snap/features/[active]refactor_to_cli.md` Phase 4 "Milestone check". The notebook
salvage (`+notebooks/`) is handled separately by `[draft]notebooks-clean-rebuild`.
