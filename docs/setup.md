# Setup

How to install and run **minutia**. The primary, recommended way to use it is as a
[`uv` tool](https://docs.astral.sh/uv/guides/tools/) — a globally available `minutia`
command in its own isolated environment, independent of any source checkout.

## Requirements

- **[`uv`](https://docs.astral.sh/uv/)** — a recent version. uv manages the Python
  interpreter for you; you do not install Python yourself. If unsure, run `uv self update`
  (see the [interpreter note](#python-interpreter-note) for why the version matters).
- **Python `>=3.12,<3.14`** — capped because Whisper's `torch` has no `cp314` wheels yet.
  uv selects a compatible interpreter automatically (currently 3.12).
- **`ffmpeg`** on your `PATH` — used to extract audio tracks from `.mkv` recordings
  (install via your OS package manager, e.g. `apt install ffmpeg` / `brew install ffmpeg`).
- **An Anthropic API key** for summarization (`ANTHROPIC_API_KEY`).

## Install as a tool (recommended)

### Install from `main`

```bash
uv tool install git+https://github.com/NicholasGrundl/minutia@main
```

No `--python` flag is needed with a recent uv — it honors the project's
`requires-python` cap and picks a compatible interpreter (3.12) on its own.

To pin a tagged release instead of tracking `main`:

```bash
uv tool install git+https://github.com/NicholasGrundl/minutia@v0.4.0
```

### SSH alternative

If you prefer to fetch over SSH with your GitHub key:

```bash
uv tool install git+ssh://git@github.com/NicholasGrundl/minutia@main
```

### Verify

```bash
minutia --help
minutia info       # prints every resolved config value and where it came from
```

If the `minutia` console script isn't on your `PATH`, run `uv tool update-shell` (then
restart your shell), or prefix commands with `uvx --from minutia minutia ...`.

### Upgrade / reinstall / uninstall

```bash
uv tool upgrade minutia                                              # upgrade in place
uv tool install --force git+https://github.com/NicholasGrundl/minutia@main   # re-pull main
uv tool uninstall minutia
```

## Python interpreter note

minutia requires **Python `>=3.12,<3.14`**: `torch` (pulled in by Whisper) ships no
`cp314` wheels yet, so 3.14 cannot resolve. With a current uv, `uv tool install` reads
this cap and automatically selects 3.12 (or 3.13, if installed) — **do not pass
`--python`**.

Older uv releases (observed on `0.9.x`) did **not** honor the cap during interpreter
selection for git/local installs: they reached for the newest interpreter on the machine
(3.14) and failed to resolve `torch`, forcing a manual `--python 3.12`. If you hit that,
in order of preference:

1. `uv self update`, then reinstall — this is the real fix (verified on uv `0.12.x`).
2. `uv python uninstall 3.14` — remove the interpreter torch can't use anyway.
3. `UV_PYTHON=3.12 uv tool install git+https://github.com/NicholasGrundl/minutia@main`.

## Runtime configuration

- `ANTHROPIC_API_KEY=sk-ant-...` — required before summarizing.
- Optional `MINUTIA_*` environment variables and a platform-specific user config layer
  configure recordings/output directories, Whisper model, and more. A project-local
  `.env` is discovered from the invocation directory; `minutia --env-file PATH ...`
  selects one explicitly, `minutia --no-env-file ...` disables discovery. Run
  `minutia info` to see the resolved values and their sources.
- See **[running-the-pipeline.md](running-the-pipeline.md)** for the full walkthrough.

## Develop from a local clone

For working *on* minutia rather than just running it:

```bash
git clone https://github.com/NicholasGrundl/minutia
cd minutia
uv sync                 # create .venv and install the dev group
uv run minutia --help   # run from the clone
```

To expose an editable global command that tracks your working tree:

```bash
uv tool install --editable .
```

(No `--python` needed with a recent uv.) See the README's **Development** section for the
`just` task recipes (`just sync`, `just lint`, `just ty`, `just test`, `just check-all`).

### PyTorch build (CPU vs CUDA)

`torch` comes in transitively via Whisper. A bare `uv sync` resolves it from PyPI — the
**CUDA (GPU) build** on Linux, which is what you want for real transcription. Two extras let
you pin the build explicitly (they're mutually exclusive):

```bash
uv sync --extra cpu     # CPU-only wheels (~200 MB, no nvidia-* libs) — what CI installs
uv sync --extra cu124   # CUDA 12.4 wheels from the PyTorch index
```

CI uses `--extra cpu` because the runners have no GPU and only run the lint + type gate and
the unit tests; that avoids downloading the ~2.5 GB CUDA stack. Reproduce CI's environment locally with
`just sync-cpu`.
