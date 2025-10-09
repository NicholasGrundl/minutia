# UV-based project management for Minutia

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

# Development commands
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

.PHONY: test
test:
	@echo "Running tests..."
	uv run pytest

.PHONY: clean
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage

# Jupyter Lab
.PHONY: jupyter
jupyter: 
	@echo "Starting Jupyter Lab..."
	uv run jupyter lab --autoreload

