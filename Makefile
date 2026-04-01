.PHONY: install dev clean test venv help

PYTHON ?= python3.11

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment
	$(PYTHON) -m venv venv
	@echo "Run: source venv/bin/activate"
	@echo "Override the interpreter if needed: make venv PYTHON=python3.12"

install:  ## Install hermes-hud as a package
	$(PYTHON) -m pip install .

dev:  ## Install in editable mode for development
	$(PYTHON) -m pip install -e ".[neofetch]"

clean:  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info hermes_hud/__pycache__ hermes_hud/**/__pycache__

test:  ## Run the test suite
	$(PYTHON) -m pytest tests/ -v
