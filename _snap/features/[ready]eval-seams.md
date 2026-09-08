---
state: ready
changelog:
  "2026-09-08": "Extracted from [active]refactor_to_cli Phase 5 during the §5 spec-split
    (EXECUTIVE_SUMMARY.md)."
---

# eval-seams — SummaryClient protocol + run-metadata sidecar

## Executive Overview

Add the low-surface seams that make summarization swappable and runs reproducible — the
foundation the future `evals-harness` and `local-llm-summarization` specs build on. Two pieces,
carried verbatim from `refactor_to_cli` Phase 5.

**Non-goals:** no actual local-LLM client here (that's `[draft]local-llm-summarization`); no eval
harness / scoring (that's `[draft]evals-harness`).

## Task Checklist

- [ ] `clients/summary_client.py`: define a `SummaryClient` protocol —
      `complete(system_prompt, text, *, model, max_tokens, temperature) -> str` — plus
      `AnthropicSummaryClient`. Refactor `generate_long_summary` / `generate_summary` to accept a
      client (default Anthropic) instead of constructing one inline. TDD with a fake client.
- [ ] Run-metadata sidecar: every `summarize` run writes `<report>.run.json` beside its output
      via `run_metadata.py` — transcript path + content hash, prompt kind + prompt hash, model,
      params, token counts, estimated cost, timestamps, output path. Unit test: sidecar schema
      round-trips.

## Details

Source: `_snap/features/[active]refactor_to_cli.md` Phase 5. Anthropic client wrapping: keep the
existing cost-estimation path intact; mock the API in unit/integration tests (never a real call).
