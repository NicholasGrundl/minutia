# Roadmap

Ordered list of features to build for **minutia** — a meeting recording, transcription, and
summarization tool. The order *is* the plan; "phases" are just grouping labels. Detail for any
feature lives in its `features/<name>.md` spec; history lives in
[`DECISIONS.md`](./DECISIONS.md).

*Last updated: 2026-07-01 (unified `_blueprint`/`_snap` into a single workspace; `_snap`'s core
memory files reset for this project after being seeded from another project's content).*

---

1. **`[active]`** [`refactor_to_cli`](./features/%5Bactive%5Drefactor_to_cli.md) — finish
   migrating from the notebook/`baseline_pipeline.py` workflow to the
   `src/minutia/{pipeline,steps}/` package structure, validated against golden-sample fixtures.
   Currently mid-Phase 2 (logic unification): `baseline_pipeline.py` is still active and
   tested, not yet deletable.
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
