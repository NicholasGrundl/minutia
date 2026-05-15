# UV-based project management for Minutia
#
# This Makefile is the primary task runner for development commands.
# You can use either:
#   - make <target>           (recommended, convenient)
#   - uv run <command> <args> (direct command execution)

PYTHON_VENV := .venv/bin/python
PYTEST_ARGS ?=

# Installation commands (UV native, not scripts)
# Note: `uv sync` installs the `dev` group by default (PEP 735).
.PHONY: install
install:
	@echo "Installing project + dev group (default)..."
	uv sync

.PHONY: install-jupyter
install-jupyter:
	@echo "Installing project + dev + jupyter groups..."
	uv sync --group jupyter

.PHONY: install-all
install-all:
	@echo "Installing project with all dependency groups..."
	uv sync --all-groups

.PHONY: create-env-file
create-env-file:
	@echo "Creating .env file..."
	@if [ ! -f .env ]; then \
		echo "# API Keys" > .env; \
		echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env; \
		echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env; \
		echo ".env file created. Please edit it with your actual API keys."; \
	else \
		echo ".env file already exists. Please ensure it contains your API keys."; \
	fi

# Code quality commands
.PHONY: lint
lint:
	@echo "Running linter..."
	uv run ruff check .

.PHONY: format
format:
	@echo "Formatting code..."
	uv run ruff format .

.PHONY: lint-fix
lint-fix:
	@echo "Running linter with auto-fix..."
	uv run ruff check --fix .

.PHONY: check-all
check-all:
	@echo "Running lint-fix, format, and test..."
	@$(MAKE) lint-fix
	@$(MAKE) format
	@$(MAKE) test

# Testing commands
.PHONY: test
test:
	@echo "Running tests via uv..."
	uv run pytest

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	uv run pytest -m unit

.PHONY: test-integration
test-integration:
	@echo "Running unit and integration tests..."
	uv run pytest -m "unit or integration"

.PHONY: test-all
test-all:
	@echo "Running all tests including slow..."
	uv run pytest -m "unit or integration or slow"

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	uv run pytest --cov=src/minutia --cov-report=html --cov-report=term

.PHONY: test-cleanup
test-cleanup:
	@echo "Removing test artifacts..."
	rm -rf .coverage .coverage.* coverage.xml htmlcov/ .pytest_cache/

# Development commands
.PHONY: clean
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage

.PHONY: jupyter
jupyter:
	@echo "Starting Jupyter Lab..."
	uv run jupyter lab --autoreload

# Help command
.PHONY: help
help:
	@echo "Minutia Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install core + dev group (default)"
	@echo "  make install-jupyter  Install core + dev + jupyter groups"
	@echo "  make install-all      Install everything (all dependency groups)"
	@echo "  make create-env-file  Create .env file template"
	@echo ""
	@echo "  For individual groups: uv sync --group <name>"
	@echo "  Available groups: dev, jupyter, diagnostics, experiments, media"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Check code with ruff"
	@echo "  make lint-fix         Auto-fix linting issues"
	@echo "  make format           Format code with ruff"
	@echo "  make check-all        Run lint-fix + format + test"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-codex       Run tests via local .venv (offline-friendly)"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run unit + integration tests"
	@echo "  make test-all         Run all tests including slow"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-cleanup     Remove pytest and coverage artifacts"
	@echo ""
	@echo "Development:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make jupyter          Start Jupyter Lab"
	@echo ""
	@echo "Note: This Makefile is the primary task runner."
	@echo "You can also run commands directly: uv run <command> <args>"


# LLM committing

.PHONY: commit
commit:
	@echo "Committing changes with LLM summarization..."
	.claude/hooks/macro-commit.sh --force

# Codex specific (permissions issues for calling uv run in sandbox)

.PHONY: test-codex
test-codex:
	@echo "Running tests via local .venv..."
	LOGURU_LEVEL=INFO .venv/bin/python -m pytest tests/ -v


.PHONY: lint-codex
lint-codex:
	@echo "Running tests via local .venv..."
	.venv/bin/python -m ruff check .
