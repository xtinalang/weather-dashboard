# Makefile for weather_app

.PHONY: run-flask run-typer install clean package all

# Variables
PYTHON = python
PIP = pip
PORT = 5001
FLASK_APP = web.app

# Default target
all: install run-flask

# Run the Flask application using uv
run-flask:
	FLASK_PORT=$(PORT) uv run python -m web &

# Run the Typer CLI
run-typer:
	$(PYTHON) -m weather_app.cli

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Package the application
package: clean
	$(PYTHON) setup.py sdist bdist_wheel
