# UV-based project management for Minutia
#
# This Makefile is the primary task runner for development commands.
# Note: UV does not support tool.uv.scripts, so we use Make for task running.
#
# You can use either:
#   - make <target>           (recommended, convenient)
#   - uv run <command> <args> (direct command execution)

# Installation commands (UV native, not scripts)
.PHONY: install
install:
	@echo "Installing project and dependencies with uv..."
	uv sync

.PHONY: install-dev
install-dev:
	@echo "Installing project with development dependencies..."
	uv sync --extra dev

.PHONY: install-all
install-all:
	@echo "Installing project with all optional dependencies..."
	uv sync --extra dev --extra jupyter --extra media

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
	@echo "Running tests..."
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
	@echo "  make install          Install core dependencies"
	@echo "  make install-dev      Install with dev dependencies (ruff, pytest)"
	@echo "  make install-all      Install everything (dev, jupyter, media)"
	@echo "  make create-env-file  Create .env file template"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Check code with ruff"
	@echo "  make lint-fix         Auto-fix linting issues"
	@echo "  make format           Format code with ruff"
	@echo "  make check-all        Run lint-fix + format + test"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run unit + integration tests"
	@echo "  make test-all         Run all tests including slow"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make jupyter          Start Jupyter Lab"
	@echo ""
	@echo "Note: All commands use UV scripts defined in pyproject.toml"
	@echo "You can also run directly: uv run <script-name>"

