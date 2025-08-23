# Makefile for ARCVDE development

.PHONY: help install install-dev lint format security clean run

help:
	@echo "Available commands:"
	@echo "  make install      - Install project dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make lint         - Run all linting checks"
	@echo "  make format       - Auto-format code with black and isort"
	@echo "  make security     - Run security and vulnerability scans"
	@echo "  make clean        - Remove generated files and caches"
	@echo "  make run          - Run the game"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

lint:
	@echo "Running Black (formatting check)..."
	black --check --diff src/ main.py sound_generation/
	@echo "\nRunning isort (import sorting check)..."
	isort --check-only --diff src/ main.py sound_generation/
	@echo "\nRunning Flake8 (linting)..."
	flake8 .

format:
	@echo "Formatting code with Black..."
	black src/ main.py sound_generation/
	@echo "\nSorting imports with isort..."
	isort src/ main.py sound_generation/
	@echo "\nFormatting complete!"

security:
	@echo "Running Safety (vulnerability check)..."
	-safety check
	@echo "\nRunning Bandit (security linter)..."
	-bandit -r src/ -f screen
	@echo "\nRunning pip-audit..."
	-pip-audit --desc
	@echo "\nSecurity scan complete!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

run:
	python main.py