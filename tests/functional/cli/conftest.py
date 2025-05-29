"""Pytest configuration and fixtures for CLI functional tests."""

import os
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def cli_command() -> str:
    """Base CLI command for testing."""
    return "python -m weather_app.cli"


@pytest.fixture
def temp_env(monkeypatch) -> Generator[None, None, None]:
    """Create a temporary environment for testing."""
    # Create temporary database path for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = Path(temp_dir) / "test_weather.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{temp_db_path}")
        yield


@pytest.fixture
def run_cli() -> callable:
    """Fixture to run CLI commands and capture output."""

    def _run_cli(command: str, input_text: str = None, timeout: int = 30) -> dict:
        """
        Run a CLI command and return the result.

        Args:
            command: The full command to run
            input_text: Optional input to send to the command
            timeout: Command timeout in seconds

        Returns:
            dict with 'returncode', 'stdout', 'stderr'
        """
        try:
            process = subprocess.run(
                command.split(),
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent.parent.parent,  # Project root
            )
            return {
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Error running command: {str(e)}",
            }

    return _run_cli


@pytest.fixture
def mock_env_with_api_key(monkeypatch) -> None:
    """Set up environment with API key for testing."""
    # Use a test API key or the real one if available
    api_key = os.getenv("WEATHER_API_KEY", "test-api-key")
    monkeypatch.setenv("WEATHER_API_KEY", api_key)


@pytest.fixture
def cli_args_base() -> list[str]:
    """Base CLI arguments for consistent testing."""
    return ["python", "-m", "weather_app.cli"]
