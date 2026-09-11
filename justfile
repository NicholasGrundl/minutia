# Minutia task runner. Run `just` or `just --list` to see recipes.
#
# Replaces the former Makefile. Commands can also be run directly, e.g.
# `uv run pytest` instead of `just test`.

# Default: list available recipes
default:
    @just --list

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Install/sync the environment (dev group + CUDA torch — the GPU build from PyPI)
sync:
    uv sync

# Sync with the CPU-only torch build (no CUDA/nvidia libs) — what CI runs
sync-cpu:
    uv sync --extra cpu

# Install/sync with all dependency groups (dev, jupyter, diagnostics, experiments, media)
sync-all:
    uv sync --all-groups

# Scaffold a .env template with API-key placeholders (won't overwrite an existing .env)
create-env-file:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f .env ]; then
        echo ".env file already exists. Please ensure it contains your API keys."
    else
        printf '# API Keys\n' > .env
        printf 'OPENAI_API_KEY=your_openai_api_key_here\n' >> .env
        printf 'ANTHROPIC_API_KEY=your_anthropic_api_key_here\n' >> .env
        echo ".env file created. Please edit it with your actual API keys."
    fi

# ---------------------------------------------------------------------------
# Tool install
# ---------------------------------------------------------------------------

# Reinstall the minutia CLI tool from the latest main on GitHub
reinstall:
    uv tool install --force git+https://github.com/NicholasGrundl/minutia@main

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

# Format code and apply all safe lint fixes (mutating) — package source + tests
ruff:
    uv run ruff format src tests
    uv run ruff check --fix src tests

# Type check (read-only — ty has no autofix; errors need manual edits)
# Scope is set by [tool.ty.src] in pyproject.toml (src + tests).
ty:
    uv run ty check

# Dev gate: mutating ruff, then ty, then the test suite
ci: ruff ty

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

# Run the test suite; forward pytest args, e.g. `just test -k merge`
test *args:
    uv run pytest {{args}}

# Unit tests only (fast)
test-unit:
    uv run pytest -m unit

# Unit + integration tests
test-integration:
    uv run pytest -m "unit or integration"

# All tests including slow (full pipeline)
test-all:
    uv run pytest -m "unit or integration or slow"

# Tests with coverage report (terminal + HTML)
test-cov:
    uv run pytest --cov=src/minutia --cov-report=html --cov-report=term

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------
# Bump the version, commit, tag, and push — pushing the v* tag triggers the
# release workflow (.github/workflows/release.yml). Preview first with
# `uv run python scripts/release.py patch -n`.

# Cut a patch release (e.g. 0.1.0 -> 0.1.1): bump, commit, tag, push.
tag-patch:
    uv run python scripts/release.py patch

# Cut a minor release (e.g. 0.1.0 -> 0.2.0): bump, commit, tag, push.
tag-minor:
    uv run python scripts/release.py minor

# Cut a major release (e.g. 0.1.0 -> 1.0.0): bump, commit, tag, push.
tag-major:
    uv run python scripts/release.py major

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

# Start Jupyter Lab with autoreload
jupyter:
    uv run jupyter lab --autoreload

# Remove build + test artifacts
clean:
    rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage .coverage.* coverage.xml
