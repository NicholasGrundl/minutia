# Define variables
CONDA_ENV_NAME := notetaker
PYTHON_VERSION := 3.10

# Manage Conda Envrionment
.PHONY: create
create: requirements.txt conda_packages.txt create_env_conda create_env_file 

.PHONY: create_env_conda
create_env_conda:
	@echo "Creating conda environment..."
	conda create -n $(CONDA_ENV_NAME) python=$(PYTHON_VERSION) pip -y
	@echo "Installing conda packages..."
	conda install -n $(CONDA_ENV_NAME) --file conda_packages.txt -y

.PHONY: remove_env_conda
remove_env_conda:
	@echo "Removing conda environment..."
	conda remove --name $(CONDA_ENV_NAME) --all -y



.PHONY: create_env_file
create_env_file:
	@echo "Creating .env file..."
	@if [ ! -f .env ]; then \
		echo "# API Keys" > .env; \
		echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env; \
		echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env; \
		echo ".env file created. Please edit it with your actual API keys."; \
	else \
		echo ".env file already exists. Please ensure it contains your API keys."; \
	fi

# Python Dependency management
.PHONY: install
install: 
	pip install -r ./requirements.txt
	pip freeze > requirements-lock.txt
	@echo "Pinned requirements exported to requirements-lock.txt"

.PHONY: uninstall
uninstall:
	@bash -c "pip uninstall -y -r <(pip freeze)"
	@if [ -f requirements-lock.txt ]; then \
		rm requirements-lock.txt; \
		echo "Removed requirements-lock.txt"; \
	fi

#### Jupyter ####
.PHONY: jupyter
jupyter: 
	@jupyter lab --autoreload

