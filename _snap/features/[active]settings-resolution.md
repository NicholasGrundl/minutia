---
state: active
changelog:
  "2026-09-08 BUILD": "Scoped after the test-refactor investigation exposed production config
    state leakage. Agreed on Pydantic Settings, a platformdirs global config, cwd-contextual
    dotenv discovery, explicit CLI overrides, and a strict boundary from future pipeline DSLs."
---

# Settings resolution

## Executive overview

Replace the hand-written, stateful configuration loader with a validated Pydantic Settings
boundary. The refactor should make ordinary `minutia` invocations predictable when the CLI is
installed globally as a uv tool, retain useful provenance in `minutia config`, and remove the
`load_dotenv()` mutation that currently lets one config load affect later calls and tests.

This feature covers application settings only. A pipeline file is a separate domain object for
describing reproducible workflows and experiments; it may overlay selected settings when a run is
assembled, but it is not another settings file and is not implemented here.

## Configuration model

The concepts are intentionally separate:

| Concept | Role | Examples |
|---|---|---|
| Application settings | Stable day-to-day preferences | default models, track numbers, recordings/output directories, log level |
| Secrets/context | Session- or project-specific values | API keys, project output directory, temporary model choice |
| CLI overrides | One-invocation changes | input/output paths, model, track, force behavior |
| Pipeline specification | Reproducible workflow/experiment | steps, prompt/model matrix, eval inputs, explicit per-run overrides |

`MinutiaSettings` owns validated application settings. Provenance/discovery metadata remains a
separate resolution concern so the model does not accumulate loader bookkeeping.

## Source precedence

Normal command resolution, weakest to strongest:

```text
built-in defaults
    < platformdirs user config
    < contextual .env
    < process environment
    < CLI arguments
```

For a future pipeline invocation:

```text
built-in defaults
    < platformdirs user config
    < contextual .env
    < process environment
    < explicit pipeline values
    < CLI arguments
```

An omitted pipeline field inherits ordinary settings; an explicit pipeline value wins so the
experiment is reproducible. Pipeline files must not contain API keys.

## Persistent global configuration

- Fixed location: `platformdirs.user_config_path("minutia") / "config.env"`.
- Intended for durable personal defaults, not per-project behavior or secrets.
- The file may later be created by `minutia init`; automatic interactive initialization is
  deferred. Any future wizard must not surprise scripts or non-interactive commands.
- File absence is valid and means built-in defaults apply.

## Contextual `.env` discovery

Automatic discovery is anchored to the shell invocation directory. Input and output paths are
data locations and never alter configuration discovery.

1. `--env-file PATH` selects exactly that file and bypasses discovery.
2. `--no-env-file` disables contextual dotenv loading.
3. Otherwise begin at `Path.cwd()` and walk upward.
4. Load only the nearest `.env`; never merge an ancestor chain.
5. Stop after checking the first project boundary (`.git` or `pyproject.toml`).
6. Outside a marked project, stop before the user's home directory so `~/.env` is never loaded
   implicitly.
7. Only declared Minutia fields and supported API-key aliases are consumed; unrelated dotenv
   keys are ignored.

The installed uv tool environment is irrelevant to discovery: the executable inherits the
caller's working directory, which expresses the desired project context.

## Relative-path semantics

Paths are anchored to the source that declared them:

- platformdirs config values: relative to the global config directory;
- contextual `.env` values: relative to the selected `.env` file;
- future pipeline values: relative to the pipeline file;
- process-environment and CLI values: relative to the invocation directory.

This makes a project `.env` or pipeline file portable and prevents behavior from changing merely
because the command was launched from a nested directory.

## Build plan

- [x] **Characterize the contract first** — add focused tests for precedence, API-key aliases,
      validation, no process-environment mutation, provenance, explicit/disabled dotenv files,
      nearest-file discovery, boundary stopping, and per-source relative paths.
- [x] **Add `pydantic-settings`** — make it a direct runtime dependency and use current official
      Pydantic Settings APIs. Remove the direct `python-dotenv` dependency only if no project code
      imports it after the migration.
- [x] **Implement discovery as a Minutia policy** — a small pure function accepts an invocation
      directory and optional explicit/disabled selection, returning the chosen contextual file.
      Do not rely on Pydantic's implicit cwd lookup for boundary behavior.
- [x] **Define validated settings** — replace the mutable dataclass/coercion functions with a
      `BaseSettings` model: `MINUTIA_` prefix, typed paths/enums/integers, model and log-level
      validation, and supported aliases for the Anthropic key. Remove the config-to-orchestrator
      import; model validation comes from `model_registry.py`.
- [x] **Compose sources without global mutation** — resolve defaults, global config, contextual
      dotenv, process environment, and initialization/CLI values in the agreed order. Delete
      `_load_env_files()` and all `load_dotenv()` calls.
- [x] **Keep resolution observable** — return or retain separate source metadata sufficient for
      `minutia config` to show each effective value, its winning source, the global config path,
      the contextual discovery anchor, and the selected `.env`. Continue masking secrets.
- [x] **Expose global CLI controls** — add `--env-file PATH` and `--no-env-file` at the Typer app
      callback so configuration is selected before any subcommand runs. Existing command flags
      remain the final, highest-precedence overrides.
- [x] **Remove API-key side doors** — consumers receive the resolved key/settings explicitly;
      `resolve_anthropic_api_key()` must not independently reread mutable global state. Keep a
      compatibility shim only if a current caller genuinely requires it during migration.
- [x] **Harden test isolation** — scrub ambient `MINUTIA_*`, `ANTHROPIC_API_KEY`, and legacy key
      aliases before each test, then opt tests into explicit values. Re-enable the skipped
      no-recordings-dir CLI test. This protects tests from legitimate process-environment input;
      it is separate from eliminating loader mutation.
- [x] **Update user-facing documentation** — document the effective tree, discovery policy,
      relative-path behavior, global CLI controls, and recommended placement of secrets. Remove
      `.minutia` from the documented source chain.
- [x] **Verify proportionally** — run focused config/CLI tests, then the unit suite, then the
      timeout-guarded suite. The five stale orchestrator e2e failures remain separately scoped.

## Acceptance criteria

- Repeated config loads are deterministic and never mutate `os.environ`.
- A globally installed `minutia` command resolves context from the caller's cwd.
- Global, contextual, process, and CLI values obey the documented precedence.
- Relative paths behave consistently with their source file or invocation context.
- `minutia config` accurately identifies winning sources without revealing secrets.
- Ambient developer configuration cannot make tests select real recordings or services.
- No production adapter, alias, or pipeline API is added solely to satisfy a stale test.

## Explicit non-goals

- Designing or parsing the YAML/JSON pipeline DSL.
- Refactoring `PipelineConfig` or repairing the five stale e2e pipeline tests.
- Building the one-time initialization wizard.
- Exposing every provider/model tuning parameter as a CLI flag in this slice.
