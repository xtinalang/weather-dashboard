# Makefile for weather_app

.PHONY: run-flask run-typer install clean package all lint test security check-all ci-dev ci-prod

# Variables
PYTHON = python
PIP = pip
PORT = 5001
FLASK_APP = web.app

# Default target
all: install run-flask

# Run the Flask application using uv
run-flask:
	uv run flask --app web.app --debug run --port=$(PORT)


# Run the Typer CLI
run-typer:
	$(PYTHON) -m weather_app.cli interactive

# Install dependencies
install:
	uv pip install -e .

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Package the application
package: clean
	uv build

# Linting and formatting
lint:
	@echo "🔍 Running linting checks..."
	uv run ruff check .
	uv run ruff format --check .
	uv run flake8 .
	uv run mypy weather_app/ || echo "⚠️ MyPy found issues"

# Fix linting issues
lint-fix:
	@echo "🔧 Fixing linting issues..."
	uv run ruff check . --fix
	uv run ruff format .

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest --verbose --tb=short

# Run tests with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	uv run coverage run -m pytest
	uv run coverage report
	uv run coverage html

# Security scanning
security:
	@echo "🔒 Running security scans..."
	uv add safety bandit --dev
	uv run safety check
	uv run bandit -r weather_app/

# Pre-commit hooks
pre-commit:
	@echo "🔗 Running pre-commit hooks..."
	uv run pre-commit run --all-files

# Run all quality checks (like CI development)
check-all: lint test security pre-commit
	@echo "✅ All quality checks passed!"

# Run CI development checks locally
ci-dev: check-all
	@echo "🚀 Development CI checks complete!"

# Run CI production checks locally
ci-prod: lint test-coverage security
	@echo "📦 Building package..."
	uv build
	@echo "🧪 Testing package installation..."
	uv add dist/*.whl
	uv run weather-dashboard --help
	@echo "🚀 Production CI checks complete!"
