"""
Configuration file for pytest.
This file contains shared fixtures and configurations that can be used by all test files.
"""

import os
import sys

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# This allows the tests to import weather_app modules properly


# You can define shared fixtures here that will be available to all test files
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup any environment variables needed for testing."""
    # Set to test mode
    os.environ["TESTING"] = "True"

    # Use SQLite for testing
    if "WEATHER_APP_DATABASE_URL" not in os.environ:
        os.environ["WEATHER_APP_DATABASE_URL"] = "sqlite:///:memory:"

    yield

    # Clean up
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
