# UV-based project management for Minutia
#
# This Makefile provides convenient shortcuts to UV scripts defined in pyproject.toml
# You can use either:
#   - make <target>  (convenient, traditional)
#   - uv run <script> (direct UV invocation)
#
# All scripts are defined in [tool.uv.scripts] section of pyproject.toml

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

# Code quality commands (wraps UV scripts)
.PHONY: lint
lint:
	uv run lint

.PHONY: format
format:
	uv run format

.PHONY: lint-fix
lint-fix:
	uv run lint-fix

.PHONY: check-all
check-all:
	uv run check-all

# Testing commands (wraps UV scripts)
.PHONY: test
test:
	uv run test

.PHONY: test-unit
test-unit:
	uv run test-unit

.PHONY: test-integration
test-integration:
	uv run test-integration

.PHONY: test-all
test-all:
	uv run test-all

.PHONY: test-cov
test-cov:
	uv run test-cov

# Development commands (wraps UV scripts)
.PHONY: clean
clean:
	uv run clean

.PHONY: jupyter
jupyter:
	uv run jupyter

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

