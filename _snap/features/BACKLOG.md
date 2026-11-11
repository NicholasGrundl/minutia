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

### Test-suite + fixtures sprint: benchmark fixtures, synthetic data, evals-in-tests

- **Context**: 2026-11-11 — raised while planning `public-release`. The current fixtures
  (`tests/fixtures/scenarios/`) are a handful of golden samples, two of them large third-party
  media clips kept in HEAD for launch. The idea: rebuild the fixture set as a **benchmark-style
  corpus** that evals can build on, add **primitives for synthetic data generation**, and make
  the test suite *include* evals — e.g. a pytest extension or an in-`tests/` toolkit
  (working name `pyevals`) that generates synthetic data and scores pipeline outputs.
- **When**: first sprint after the repo is public. Prepares the ground for `eval-seams` →
  `evals-harness`.
- **Options**: (a) fixtures + synthetic-data primitives only, evals later; (b) a `tests/`
  toolkit that both generates data and runs evals as pytest tests; (c) a standalone pytest
  plugin. The full design is not needed yet.
- **Effort**: Medium (sprint-sized); the plugin variant is Large.
- **Decision**: 2026-11-11 — third-party fixtures stay in HEAD for launch; replacing them is
  part of this sprint, not `public-release`.

### Dev-env modernization: direnv (.envrc)

- **Context**: 2026-07-02 — user is migrating dev tooling. The **justfile** half was PROMOTED
  2026-09-08 to `features/[ready]justfile-migration.md` (also folds in `ty` adoption). What
  remains here is only the **direnv** piece: env management via `.envrc` (auto-activate the uv
  env), replacing CWD `.env` loading. Reference cached: `_snap/context/direnv/`.
- **When**: after the `justfile-migration` lands; the Phase 3 config-precedence design
  (flag > env > `.env` > user config) is direnv-friendly either way.
- **Options**: minimal `.envrc` (`layout uv` / `source .venv/bin/activate`) vs. a fuller
  `dotenv`-integrated setup.
- **Effort**: Trivial–Small.
- **Decision**: 2026-09-08 — direnv kept in BACKLOG (not bundled into the justfile migration,
  per PLAN); promote to a draft when triggered.

### Guided TUI mode for the pipeline

- **Context**: 2026-07-02 PLAN (refactor_to_cli) — the CLI gets two entry styles: power-user
  (explicit paths / latest-MKV discovery) and a *light* interactive mode (rich/typer prompts:
  pick MKV newest-first, choose prompt kind, confirm cost) built inside `refactor_to_cli`.
  A full guided TUI — persistent screens, navigation, progress views (e.g. `textual`) — was
  explicitly deferred to keep the refactor surface small.
- **When**: after `refactor_to_cli` lands and the light interactive mode's rough edges are
  known; or when onboarding a non-power-user.
- **Options**: `textual` app; or grow the rich-prompt flow incrementally.
- **Effort**: Medium-Large.
- **Decision**: 2026-07-02 — light interactive now, full TUI deferred here.

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

