---
state: draft
changelog:
  "2026-09-08": "Parked stub — split out of [draft]refactor_for_opensource_portfolio during the
    §5 scope-creep containment (EXECUTIVE_SUMMARY.md)."
---

# local-llm-summarization (parked)

## Executive Overview

A local-LLM summarization path (e.g. Ollama) as an alternative to the Anthropic API — cost-free,
offline, private summaries. Slots behind the `SummaryClient` protocol from `eval-seams`, so it's a
new client implementation rather than a pipeline rewrite. Split from the
`refactor_for_opensource_portfolio` vision.

**Depends on** `[ready]eval-seams` (the `SummaryClient` seam). **Parked** — scoped placeholder
only. Expand into a full spec in its own PLAN session when its branch is cut off `main`.
