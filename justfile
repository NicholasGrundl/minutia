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

# Install/sync the environment (default dev group)
sync:
    uv sync

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
# Code quality
# ---------------------------------------------------------------------------

# Lint (read-only) — scoped to package source
lint:
    uv run ruff check src

# Format code — scoped to package source
format:
    uv run ruff format src

# Format code and apply all safe lint fixes (mutating) — scoped to package source
ruff:
    uv run ruff format src
    uv run ruff check --fix src

# Type check (read-only — ty has no autofix; errors need manual edits)
# Scope is set by [tool.ty.src] in pyproject.toml (src). Tests are gated in a
# future tests-refactor feature.
ty:
    uv run ty check

# Dev gate: mutating ruff, then ty, then the test suite
check-all: ruff ty test

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
# Development
# ---------------------------------------------------------------------------

# Start Jupyter Lab with autoreload
jupyter:
    uv run jupyter lab --autoreload

# Remove build + test artifacts
clean:
    rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage .coverage.* coverage.xml
