---
state: draft
changelog:
  "2026-09-08": "Parked stub — split out of [draft]refactor_for_opensource_portfolio during the
    §5 scope-creep containment (EXECUTIVE_SUMMARY.md)."
---

# evals-harness (parked)

## Executive Overview

A harness to compare transcription and summarization alternatives (quality vs. cost vs. speed)
across models/backends, using the `tests/fixtures/scenarios/` golden samples as the evaluation
set. Consumes the `eval-seams` `SummaryClient` protocol + run-metadata sidecar. Split from the
`refactor_for_opensource_portfolio` vision.

**Depends on** `[ready]eval-seams`; complements `[draft]local-llm-summarization` (a key thing to
evaluate). **Parked** — scoped placeholder only. Expand into a full spec in its own PLAN session
when its branch is cut off `main`.
