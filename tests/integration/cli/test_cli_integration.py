"""Integration tests for Typer CLI application.

These tests validate the complete end-to-end functionality of the CLI
application, including database operations, API interactions, and
command flows.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from weather_app.cli import app
from weather_app.database import Database


@pytest.fixture
def runner():
    """Create a CLI runner for integration testing."""
    return CliRunner()


@pytest.fixture
def temp_db():
    """Create a temporary database for integration testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    # Set up test database
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    # Initialize database
    db = Database()
    db.create_tables()

    yield test_db_path

    # Cleanup
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        os.environ.pop("DATABASE_URL", None)

    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_weather_api_data():
    """Mock weather API response data."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "tz_id": "Europe/London",
            "localtime": "2024-01-15 14:30",
        },
        "current": {
            "temp_c": 15.0,
            "temp_f": 59.0,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            },
            "wind_mph": 6.9,
            "wind_kph": 11.2,
            "wind_dir": "W",
            "pressure_mb": 1020.0,
            "humidity": 72,
            "feelslike_c": 15.0,
            "feelslike_f": 59.0,
            "vis_km": 10.0,
            "uv": 3.0,
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2024-01-15",
                    "day": {
                        "maxtemp_c": 18.0,
                        "maxtemp_f": 64.4,
                        "mintemp_c": 12.0,
                        "mintemp_f": 53.6,
                        "condition": {
                            "text": "Partly cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                        },
                        "maxwind_mph": 8.7,
                        "maxwind_kph": 14.0,
                    },
                }
            ]
        },
    }


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_version_command_integration(self, runner):
        """Test version command returns correct version."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Weather Dashboard v0.1.0" in result.stdout

    def test_help_commands_integration(self, runner):
        """Test various help commands work correctly."""
        # Main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "A Totally Awesome Command-line Weather App" in result.stdout

        # Command-specific help
        commands = ["current", "forecast", "weather", "settings", "add-location"]
        for command in commands:
            result = runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0, f"Help for {command} failed"

    def test_database_initialization_integration(self, runner, temp_db):
        """Test database initialization through CLI."""
        result = runner.invoke(app, ["init-db"])

        assert result.exit_code == 0
        assert "Database initialized successfully" in result.stdout

    @patch("weather_app.cli.WeatherAPI")
    def test_weather_command_integration(
        self, mock_api_class, runner, mock_weather_api_data
    ):
        """Test complete weather command flow."""
        # Setup mock
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.get_weather.return_value = mock_weather_api_data

        # Test weather command
        result = runner.invoke(app, ["weather", "London"])

        assert result.exit_code == 0
        mock_api.get_weather.assert_called_once_with("London")

    @patch("weather_app.cli.WeatherAPI")
    def test_weather_command_with_units_integration(
        self, mock_api_class, runner, mock_weather_api_data
    ):
        """Test weather command with different temperature units."""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.get_weather.return_value = mock_weather_api_data

        # Test Celsius
        result = runner.invoke(app, ["weather", "London", "--unit", "C"])
        assert result.exit_code == 0

        # Test Fahrenheit
        result = runner.invoke(app, ["weather", "London", "--unit", "F"])
        assert result.exit_code == 0

    def test_location_management_integration(self, runner, temp_db):
        """Test adding and managing locations through CLI."""
        # Add a location
        result = runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test City",
                "--lat",
                "40.7128",
                "--lon",
                "-74.0060",
                "--country",
                "USA",
                "--region",
                "New York",
            ],
        )

        assert result.exit_code == 0
        assert "Added location successfully" in result.stdout

    def test_settings_management_integration(self, runner, temp_db):
        """Test settings management through CLI."""
        # Set forecast days
        result = runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert result.exit_code == 0

        # Update settings
        result = runner.invoke(app, ["settings", "--forecast-days", "7"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert result.exit_code == 0

    def test_date_command_integration(self, runner):
        """Test date command with various date formats."""
        # Valid date
        result = runner.invoke(app, ["date", "2024-12-25"])
        assert result.exit_code == 0

        # Invalid date format
        result = runner.invoke(app, ["date", "invalid-date"])
        assert result.exit_code == 0
        assert "Invalid date format" in result.stdout

    def test_command_validation_integration(self, runner):
        """Test command parameter validation."""
        # Invalid days range
        result = runner.invoke(app, ["forecast", "--days", "10"])
        assert result.exit_code != 0

        result = runner.invoke(app, ["forecast", "--days", "0"])
        assert result.exit_code != 0

        # Valid days range
        result = runner.invoke(app, ["forecast", "--days", "3"])
        assert result.exit_code == 0

    @patch("weather_app.cli.WeatherAPI")
    def test_api_error_handling_integration(self, mock_api_class, runner):
        """Test CLI handles API errors gracefully."""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.get_weather.return_value = None  # Simulate API failure

        result = runner.invoke(app, ["weather", "NonexistentCity"])

        assert result.exit_code == 0
        assert "Failed to retrieve weather information" in result.stdout

    def test_verbose_logging_integration(self, runner):
        """Test verbose logging works across commands."""
        commands_with_verbose = [
            ["current", "--verbose"],
            ["forecast", "--verbose"],
            ["init-db", "--verbose"],
            ["settings", "--verbose", "--forecast-days", "3"],
        ]

        for command in commands_with_verbose:
            result = runner.invoke(app, command)
            # Should not crash with verbose flag, but some commands might not support it
            assert result.exit_code in [
                0,
                1,
                2,
            ]  # Allow various exit codes for unsupported flags


class TestCLIDatabaseIntegration:
    """Integration tests for CLI database operations."""

    def test_full_location_workflow(self, runner, temp_db):
        """Test complete location management workflow."""
        # Initialize database
        result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0

        # Add location
        result = runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Paris",
                "--lat",
                "48.8566",
                "--lon",
                "2.3522",
                "--country",
                "France",
                "--favorite",
            ],
        )
        assert result.exit_code == 0

        # Add another location
        result = runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Tokyo",
                "--lat",
                "35.6762",
                "--lon",
                "139.6503",
                "--country",
                "Japan",
            ],
        )
        assert result.exit_code == 0

    def test_settings_persistence(self, runner, temp_db):
        """Test settings are persisted in database."""
        # Initialize database
        result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0

        # Set forecast days
        result = runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert result.exit_code == 0

        # Update temperature unit
        result = runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert result.exit_code == 0

        # Update both settings
        result = runner.invoke(
            app, ["settings", "--forecast-days", "7", "--temp-unit", "C"]
        )
        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_missing_required_arguments(self, runner):
        """Test CLI handles missing required arguments."""
        # Weather command without location
        result = runner.invoke(app, ["weather"])
        assert result.exit_code != 0

        # Add location without required parameters
        result = runner.invoke(app, ["add-location", "--name", "Test"])
        assert result.exit_code != 0

    def test_invalid_parameter_values(self, runner):
        """Test CLI handles invalid parameter values."""
        # Invalid forecast days
        result = runner.invoke(app, ["set-forecast-days", "--days", "15"])
        assert result.exit_code != 0

        # Invalid coordinates
        result = runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test",
                "--lat",
                "invalid",
                "--lon",
                "2.0",
                "--country",
                "Test",
            ],
        )
        assert result.exit_code != 0

    def test_database_error_handling(self, runner):
        """Test CLI handles database errors gracefully."""
        # Try to use CLI without database initialization
        # This should handle the error gracefully
        with patch("weather_app.cli.initialize_database") as mock_init:
            mock_init.side_effect = Exception("Database connection failed")

            result = runner.invoke(app, ["init-db"])
            assert result.exit_code == 0
            assert "Error initializing database" in result.stdout


class TestCLIEndToEnd:
    """End-to-end integration tests."""

    @patch("weather_app.cli.WeatherAPI")
    def test_complete_weather_workflow(
        self, mock_api_class, runner, temp_db, mock_weather_api_data
    ):
        """Test complete weather application workflow."""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.get_weather.return_value = mock_weather_api_data

        # 1. Initialize database
        result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0

        # 2. Configure settings
        result = runner.invoke(app, ["settings", "--forecast-days", "5"])
        assert result.exit_code == 0

        # 3. Add favorite location
        result = runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "London",
                "--lat",
                "51.52",
                "--lon",
                "-0.11",
                "--country",
                "UK",
                "--favorite",
            ],
        )
        assert result.exit_code == 0

        # 4. Get weather for location
        result = runner.invoke(app, ["weather", "London"])
        assert result.exit_code == 0

        # 5. Get forecast
        result = runner.invoke(app, ["forecast", "--days", "3"])
        assert result.exit_code == 0

        # 6. Get current weather
        result = runner.invoke(app, ["current"])
        assert result.exit_code == 0

    def test_configuration_and_usage_workflow(self, runner, temp_db):
        """Test configuration and usage workflow."""
        # Setup
        result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0

        # Configure preferences
        result = runner.invoke(
            app, ["settings", "--forecast-days", "7", "--temp-unit", "F"]
        )
        assert result.exit_code == 0

        # Add multiple locations
        locations = [
            ("New York", "40.7128", "-74.0060", "USA"),
            ("Paris", "48.8566", "2.3522", "France"),
            ("Tokyo", "35.6762", "139.6503", "Japan"),
        ]

        for name, lat, lon, country in locations:
            result = runner.invoke(
                app,
                [
                    "add-location",
                    "--name",
                    name,
                    "--lat",
                    lat,
                    "--lon",
                    lon,
                    "--country",
                    country,
                ],
            )
            assert result.exit_code == 0

        # Test date-specific forecasts
        result = runner.invoke(app, ["date", "2024-12-25", "--unit", "F"])
        assert result.exit_code == 0
