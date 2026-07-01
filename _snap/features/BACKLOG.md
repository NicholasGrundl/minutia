# Feature Backlog

Unscheduled ideas. When one is committed, promote it to a `[draft]<name>.md` spec in this folder
and add it to [`ROADMAP.md`](../ROADMAP.md).

**Item template** (kept from the prior system — it's a good shape):

> ### <Title>
> - **Context**: what/why; current state.
> - **When**: the trigger that should pull this into active work.
> - **Options**: viable approaches (if more than one).
> - **Effort**: rough size.
> - **Decision**: (optional) any decision already taken, dated.

---

### LanceDB retrieval backend — PROMOTED 2026-06-13

Promoted to a `[draft]` spec: **`features/[draft]lancedb_retrieval_backend.md`**.
Scoped as a rankers-only swap — LanceDB becomes the base retrieval (FTS + ANN) and
vector/text store for the three rankers; `index.json`, fusion, and expansion are
untouched. Flagged A/B through 0.1.x; retire the hand-rolled path at v0.2.0.

### Fusion-weight tuning for exact-name / high-precision matches

- **Context**: 2026-06-13 — under good (Gemini) summaries, the on-the-nose file
  `LithiumHydroxide_Solubility.pdf` ranks **#1 in the topic ranker** but **#6 fused**,
  because `semantic` ranks several (legitimately relevant) SDSs higher and the weights
  average it down. Not a bug — a weighting/calibration question now that summary
  quality is no longer the bottleneck.
- **When**: if users report "the obviously-named file isn't in the top few," or when
  doing a retrieval-quality tuning pass.
- **Options**: expose/retune `lexical_weight` / `semantic_weight` / `topic_weight`
  defaults; consider a small exact-filename or title-match boost; evaluate on a few
  labelled queries against this corpus.
- **Effort**: Small.
- **Decision**: none yet.

### Prune stale `context/` subfolders (housekeeping)

- **Context**: 2026-06-15 — leftovers from the old D3 web-app era, likely irrelevant to the
  local-folder summarizer/search: `bookmarks/`, `gemini-cli/` (metrochat uses the google-genai
  SDK, not the CLI), `firecrawl/` (web scraper; metrochat is local-only), `google-iap/`,
  `antigravity-cli/`. Most are git-tracked (~24 files); `antigravity-cli/` is untracked-on-disk.
- **When**: whenever a tidy `context/` is wanted. Owner: user (will prune manually).
- **Effort**: Trivial (`git rm` the stale folders + ARCHIVE.md note).
- **Decision**: 2026-06-15 — taken off the ALIGNMENT report at user request; user handles it.

---

