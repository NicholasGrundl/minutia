---
state: draft
changelog:
  "2026-09-08": "Parked stub — split out of [draft]refactor_for_opensource_portfolio during the
    §5 scope-creep containment (EXECUTIVE_SUMMARY.md)."
---

# background-process-cli (parked)

## Executive Overview

Run long pipeline steps (transcription, summarization) as background processes so the CLI returns
immediately, with status/poll commands to check progress — instead of blocking the terminal for
the length of a Whisper run. Split from the `refactor_for_opensource_portfolio` vision; pairs with
`sql-job-tracking` for status persistence.

**Parked** — scoped placeholder only. Expand into a full spec in its own PLAN session when its
branch is cut off `main`. Do not bleed into the stable base.
