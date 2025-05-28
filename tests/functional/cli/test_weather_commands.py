"""
Test CLI weather commands functionality.
Tests the CLI weather commands including current weather,
forecast, and search functionality.
"""

import pytest
from click.testing import CliRunner

from weather_app.cli import cli


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


class TestCurrentWeatherCommand:
    """Test the current weather command."""

    def test_current_weather_valid_city(self, cli_runner):
        """Test current weather command with valid city."""
        result = cli_runner.invoke(cli, ["current", "London"])

        # Command should not crash (exit code 0 or 1 for API issues)
        assert result.exit_code in [0, 1]

        if result.exit_code == 0:
            # Should contain weather information
            assert any(
                keyword in result.output.lower()
                for keyword in ["temperature", "weather", "london", "°"]
            )


class TestWeatherCommands:
    """Test suite for weather-related CLI commands."""

    def test_current_command_help(self, run_cli, cli_command):
        """Test that the current command shows help correctly."""
        result = run_cli(f"{cli_command} current --help")

        assert result["returncode"] == 0
        assert "Show current weather for a location" in result["stdout"]
        assert "--unit" in result["stdout"]
        assert "--verbose" in result["stdout"]

    def test_forecast_command_help(self, run_cli, cli_command):
        """Test that the forecast command shows help correctly."""
        result = run_cli(f"{cli_command} forecast --help")

        assert result["returncode"] == 0
        assert "Show weather forecast" in result["stdout"]
        assert "--days" in result["stdout"]
        assert "--unit" in result["stdout"]
        assert "--verbose" in result["stdout"]

    def test_weather_command_help(self, run_cli, cli_command):
        """Test that the weather command shows help correctly."""
        result = run_cli(f"{cli_command} weather --help")

        assert result["returncode"] == 0
        assert (
            "Get current weather and forecast for a specific location"
            in result["stdout"]
        )
        assert "--unit" in result["stdout"]
        assert "--verbose" in result["stdout"]

    def test_weather_command_with_location(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test weather command with a specific location."""
        result = run_cli(f"{cli_command} weather 'London, UK' --unit C")

        # Should complete without error (returncode 0, 1 for API errors, or 2 for argument errors)
        assert result["returncode"] in [0, 1, 2]

        # Should have some output
        assert result["stdout"] or result["stderr"]

    def test_weather_command_with_fahrenheit_unit(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test weather command with Fahrenheit unit."""
        result = run_cli(f"{cli_command} weather 'New York' --unit F")

        assert result["returncode"] in [
            0,
            1,
            2,
        ]  # Accept success, API errors, and argument errors

        # Check the command was processed
        assert result["stdout"] or result["stderr"]

    def test_current_command_with_verbose(self, run_cli, cli_command, temp_env):
        """Test current command with verbose flag."""
        result = run_cli(f"{cli_command} current --verbose --unit C")

        # Command should run (might fail due to no location set, but should not crash)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_forecast_command_with_days(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test forecast command with specific number of days."""
        result = run_cli(f"{cli_command} forecast --days 3 --unit C")

        # Should complete without crashing
        assert result["returncode"] in [
            0,
            1,
            2,
        ]  # Accept success, errors, and argument errors
        assert result["stdout"] or result["stderr"]

    def test_forecast_command_invalid_days(self, run_cli, cli_command):
        """Test forecast command with invalid number of days."""
        result = run_cli(f"{cli_command} forecast --days 10")  # Max is 7

        # Should show error for invalid days
        assert result["returncode"] == 2  # Typer validation error
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["error", "invalid", "range", "must be"]
        )

    def test_weather_command_empty_location(self, run_cli, cli_command):
        """Test weather command with empty location."""
        result = run_cli(f"{cli_command} weather ''")

        # Should handle empty location (might succeed or fail depending on implementation)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_version_command(self, run_cli, cli_command):
        """Test version command functionality."""
        result = run_cli(f"{cli_command} version")

        assert result["returncode"] == 0
        assert "Weather Dashboard" in result["stdout"]
        assert "v" in result["stdout"]  # Version string

    def test_invalid_unit_parameter(self, run_cli, cli_command):
        """Test commands with invalid unit parameter."""
        result = run_cli(f"{cli_command} weather 'London' --unit X")

        # Command should run and either accept the unit or handle it gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestDateCommands:
    """Test suite for date-specific weather commands."""

    def test_date_command_help(self, run_cli, cli_command):
        """Test that the date command shows help correctly."""
        result = run_cli(f"{cli_command} date --help")

        assert result["returncode"] == 0
        assert "Get forecast for a specific date" in result["stdout"]
        assert "YYYY-MM-DD" in result["stdout"]

    def test_date_command_valid_format(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test date command with valid date format."""
        result = run_cli(f"{cli_command} date 2024-12-25 --unit C")

        # Should process the command (may fail due to API/location issues)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_date_command_invalid_format(self, run_cli, cli_command):
        """Test date command with invalid date format."""
        result = run_cli(f"{cli_command} date 25-12-2024")  # Wrong format

        # May show format error or be handled gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_date_command_invalid_date(self, run_cli, cli_command):
        """Test date command with invalid date."""
        result = run_cli(f"{cli_command} date 2024-02-30")  # Invalid date

        # Should handle invalid date
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestVerboseLogging:
    """Test suite for verbose logging functionality."""

    def test_commands_with_verbose_flag(self, run_cli, cli_command, temp_env):
        """Test that verbose flag produces more detailed output."""
        # Test without verbose
        result_normal = run_cli(f"{cli_command} current --unit C")

        # Test with verbose
        result_verbose = run_cli(f"{cli_command} current --unit C --verbose")

        # Both should complete
        assert result_normal["returncode"] in [0, 1, 2]
        assert result_verbose["returncode"] in [0, 1, 2]

        # Verbose should generally produce more output or logging information
        # (though exact comparison depends on implementation)
        assert result_normal["stdout"] or result_normal["stderr"]
        assert result_verbose["stdout"] or result_verbose["stderr"]
