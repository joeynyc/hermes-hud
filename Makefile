.PHONY: install dev clean test venv help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment
	python3 -m venv venv
	@echo "Run: source venv/bin/activate"

install:  ## Install hermes-hud as a package
	pip install .

dev:  ## Install in editable mode for development
	pip install -e ".[neofetch]"

clean:  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info hermes_hud/__pycache__ hermes_hud/**/__pycache__

test:  ## Run the test suite
	python -m pytest tests/ -v
