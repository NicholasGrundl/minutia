---
state: done
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

- [x] Run one real meeting end-to-end using only CLI commands — either the step sequence
      (`extract-audio` → `transcribe` → `merge-transcripts` → `summarize`) or `minutia go`.
      **Done 2026-09-09:** `minutia go` on a real ~2.4h recording — GPU Whisper `medium.en` on both
      tracks (739 + 299 → 1323 merged segments), then the AI-named markdown report.
- [x] Confirm the output matches notebook expectations (transcript quality, merge ordering,
      summary shape, AI-named markdown report). **Confirmed** on the real run.
- [x] Retire the notebook for daily use (stop driving work from it); log the retirement in
      `_snap/DECISIONS.md`. **Done** — CLI is the daily driver; notebooks remain a documented
      fallback until `notebooks-clean-rebuild` (README still links them).
- [x] Flip `refactor_to_cli` → `[done]` (its own rename step). **Done** (plain `mv`, this session).

**Dogfood finding (fixed):** the `go` notes prompt silently required a *file path*; typing prose
raised `Notes file not found`. Fixed to accept inline text OR a path (`_resolve_notes_answer`,
persists inline notes to `<output_dir>/notes.md`), with a unit test.

## Details

Source: `_snap/features/[active]refactor_to_cli.md` Phase 4 "Milestone check". The notebook
salvage (`+notebooks/`) is handled separately by `[draft]notebooks-clean-rebuild`.
