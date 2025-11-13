.PHONY: install dev run clean help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Install development dependencies
	uv sync --all-extras

run: ## Run the main application
	uv run main.py

clean: ## Clean up generated files
	rm -rf .venv
	rm -rf __pycache__
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

test: ## Run tests (placeholder for future)
	@echo "No tests configured yet"

format: ## Format code (placeholder for future)
	@echo "No formatter configured yet"

lint: ## Lint code (placeholder for future)
	@echo "No linter configured yet"