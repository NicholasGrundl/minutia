---
state: ready
changelog:
  "2026-09-08": "Extracted from [active]refactor_to_cli Phase 6 during the §5 spec-split
    (EXECUTIVE_SUMMARY.md)."
---

# orchestrator-retire-baseline — orchestrator hardening + delete `baseline_pipeline.py`

## Executive Overview

Bring `PipelineOrchestrator` up to CLI parity, then delete the standalone
`baseline_pipeline.py` (still present, and — until the deferred doc pass — still the entry point
documented in `README.md`). Carried from `refactor_to_cli` Phase 6.

**Non-goals:** no new pipeline features; strictly wiring the orchestrator through the same
prompt-registry + `generate_long_summary` + report path the CLI already uses, then removing the
now-redundant baseline script.

## Task Checklist

- [ ] Add `prompt_kind`, `notes_path`, `personal_info_path`, `generate_markdown` to
      `PipelineConfig`; wire the summarize step through the CLI's prompt-registry +
      `generate_long_summary` + report path.
- [ ] End-to-end test: `PipelineOrchestrator` on a fixture scenario produces the summary, the
      `.md` report, and the run-metadata sidecar (depends on `eval-seams`).
- [ ] Update `README.md` to document the CLI as the entry point (removing `baseline_pipeline.py`).
      *Coordinate with the deferred stabilization doc pass — this README change is coupled to the
      code deletion below, not general polish.*
- [ ] Delete `src/minutia/baseline_pipeline.py` + `tests/integration/test_baseline_pipeline.py`
      once the above passes — **not before**. (Its own `git rm` step.)

## Details

Source: `_snap/archive/features/[done]refactor_to_cli.md` Phase 6. Depends on `eval-seams` (the e2e test
asserts the run-metadata sidecar). This is the spec that finally retires the pre-orchestrator
script path.
