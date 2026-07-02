# Roadmap

Ordered list of features to build for **minutia** — a meeting recording, transcription, and
summarization tool. The order *is* the plan; "phases" are just grouping labels. Detail for any
feature lives in its `features/<name>.md` spec; history lives in
[`DECISIONS.md`](./DECISIONS.md).

*Last updated: 2026-07-02 (re-planned `refactor_to_cli` against the real daily workflow,
`SummaryPromptVariations.ipynb`; previously 2026-07-01: unified `_blueprint`/`_snap` into a
single workspace).*

---

1. **`[active]`** [`refactor_to_cli`](./features/%5Bactive%5Drefactor_to_cli.md) — finish
   migrating the notebook workflow into the `src/minutia/{pipeline,steps}/` package + CLI,
   validated against golden-sample fixtures. Re-planned 2026-07-02: parity target is now
   `SummaryPromptVariations.ipynb` (the actual daily driver, which already runs on
   `minutia.steps.*`); includes low-surface eval seams (`SummaryClient` protocol,
   run-metadata sidecar). Phases 0-2 DONE (2026-07-02: prompt registry, notebook re-point,
   report-helper move, merger verified vs goldens). Next: Phase 3 CLI Foundations
   (click→typer, platformdirs defaults); `baseline_pipeline.py` still active and tested,
   not deletable until Phase 6.
2. **`[draft]`** [`refactor_for_opensource_portfolio`](./features/%5Bdraft%5Drefactor_for_opensource_portfolio.md) —
   broader post-refactor vision: filestore for videos, SQL-backed job/transcript tracking,
   background-process CLI, local-LLM summarization support, and an evals harness for comparing
   transcription/summarization alternatives.
3. **`[backlog]`** open-source release prep — see `opensource_polishing.md` at the repo root
   for the full audit. Remaining big items: notebook-output history scrub + a scoped
   `git-filter-repo` pass (vendored SDK removal + notebook transcripts), and a repo-visibility
   decision.

## Known issues (not yet worth their own feature; tracked here until triaged)

- FFmpeg audio extraction may fail on re-run if output files already exist (missing overwrite
  flag) — see the `refactor_to_cli` spec's Known Issues section.
