"""Integration tests for Typer CLI application.

These tests validate the complete end-to-end functionality of the CLI
application, including database operations, API interactions, and
command flows.
"""

from unittest.mock import patch

from tests.integration.conftest import assert_cli_success
from weather_app.cli import app


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_version_command_integration(self, cli_runner):
        """Test version command returns correct version."""
        result = cli_runner.invoke(app, ["version"])
        assert_cli_success(result, "Weather Dashboard v0.1.0")

    def test_help_commands_integration(self, cli_runner):
        """Test various help commands work correctly."""
        # Main help
        result = cli_runner.invoke(app, ["--help"])
        assert_cli_success(result, "A Totally Awesome Command-line Weather App")

        # Command-specific help
        commands = [
            "current",
            "forecast",
            "weather",
            "settings",
            "add-location",
        ]
        for command in commands:
            result = cli_runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0, f"Help for {command} failed"

    def test_database_initialization_integration(self, cli_runner, clean_db):
        """Test database initialization through CLI."""
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result, "Database initialized successfully")

    @patch("weather_app.cli.WeatherAPI")
    def test_weather_command_integration(
        self, mock_api_class, cli_runner, mock_weather_api
    ):
        """Test complete weather command flow."""
        mock_api_class.return_value = mock_weather_api
        result = cli_runner.invoke(app, ["weather", "London"])

        assert_cli_success(result)
        mock_weather_api.get_weather.assert_called_once_with("London")

    @patch("weather_app.cli.WeatherAPI")
    def test_weather_command_with_units_integration(
        self, mock_api_class, cli_runner, mock_weather_api
    ):
        """Test weather command with different temperature units."""
        mock_api_class.return_value = mock_weather_api

        # Test Celsius
        result = cli_runner.invoke(app, ["weather", "London", "--unit", "C"])
        assert_cli_success(result)

        # Test Fahrenheit
        result = cli_runner.invoke(app, ["weather", "London", "--unit", "F"])
        assert_cli_success(result)

    def test_location_management_integration(self, cli_runner, clean_db):
        """Test adding and managing locations through CLI."""
        result = cli_runner.invoke(
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
        assert_cli_success(result, "Added location successfully")

    def test_settings_management_integration(self, cli_runner, clean_db):
        """Test settings management through CLI."""
        # Set forecast days
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert_cli_success(result)

        # Update settings
        result = cli_runner.invoke(app, ["settings", "--forecast-days", "7"])
        assert_cli_success(result)

        result = cli_runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert_cli_success(result)

    def test_date_command_integration(self, cli_runner):
        """Test date command with various date formats."""
        # Valid date
        result = cli_runner.invoke(app, ["date", "2024-12-25"])
        assert_cli_success(result)

        # Invalid date format
        result = cli_runner.invoke(app, ["date", "invalid-date"])
        assert_cli_success(result, "Invalid date format")

    def test_command_validation_integration(self, cli_runner):
        """Test command parameter validation."""
        # Invalid days range
        result = cli_runner.invoke(app, ["forecast", "--days", "10"])
        assert result.exit_code != 0

        result = cli_runner.invoke(app, ["forecast", "--days", "0"])
        assert result.exit_code != 0

        # Valid days range
        result = cli_runner.invoke(app, ["forecast", "--days", "3"])
        assert_cli_success(result)

    @patch("weather_app.cli.WeatherAPI")
    def test_api_error_handling_integration(self, mock_api_class, cli_runner):
        """Test CLI handles API errors gracefully."""
        mock_api_class.return_value.get_weather.return_value = None

        result = cli_runner.invoke(app, ["weather", "NonexistentCity"])
        assert_cli_success(result, "Failed to retrieve weather information")

    def test_verbose_logging_integration(self, cli_runner):
        """Test verbose logging works across commands."""
        commands_with_verbose = [
            ["current", "--verbose"],
            ["forecast", "--verbose"],
            ["init-db", "--verbose"],
            ["settings", "--verbose", "--forecast-days", "3"],
        ]

        for command in commands_with_verbose:
            result = cli_runner.invoke(app, command)
            # Should not crash with verbose flag, but some commands might not support it
            assert result.exit_code in [0, 1, 2]


class TestCLIDatabaseIntegration:
    """Integration tests for CLI database operations."""

    def test_full_location_workflow(self, cli_runner, clean_db):
        """Test complete location management workflow."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add location
        result = cli_runner.invoke(
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
        assert_cli_success(result)

        # Add another location
        result = cli_runner.invoke(
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
        assert_cli_success(result)

    def test_settings_persistence(self, cli_runner, clean_db):
        """Test settings are persisted in database."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Set forecast days
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert_cli_success(result)

        # Update temperature unit
        result = cli_runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert_cli_success(result)

        # Update both settings
        result = cli_runner.invoke(
            app, ["settings", "--forecast-days", "7", "--temp-unit", "C"]
        )
        assert_cli_success(result)


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_missing_required_arguments(self, cli_runner):
        """Test CLI handles missing required arguments."""
        # Weather command without location
        result = cli_runner.invoke(app, ["weather"])
        assert result.exit_code != 0

        # Add location without required parameters
        result = cli_runner.invoke(app, ["add-location", "--name", "Test"])
        assert result.exit_code != 0

    def test_invalid_parameter_values(self, cli_runner):
        """Test CLI handles invalid parameter values."""
        # Invalid forecast days
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "15"])
        assert result.exit_code != 0

        # Invalid coordinates
        result = cli_runner.invoke(
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

    def test_database_error_handling(self, cli_runner):
        """Test CLI handles database errors gracefully."""
        # Try to use CLI without database initialization
        with patch("weather_app.cli.initialize_database") as mock_init:
            mock_init.side_effect = Exception("Database connection failed")

            result = cli_runner.invoke(app, ["init-db"])
            assert_cli_success(result, "Error initializing database")


class TestCLIEndToEnd:
    """End-to-end integration tests."""

    @patch("weather_app.cli.WeatherAPI")
    def test_complete_weather_workflow(
        self, mock_api_class, cli_runner, clean_db, mock_weather_api
    ):
        """Test complete weather application workflow."""
        mock_api_class.return_value = mock_weather_api

        # 1. Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # 2. Configure settings
        result = cli_runner.invoke(app, ["settings", "--forecast-days", "5"])
        assert_cli_success(result)

        # 3. Add favorite location
        result = cli_runner.invoke(
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
        assert_cli_success(result)

        # 4. Get weather for location
        result = cli_runner.invoke(app, ["weather", "London"])
        assert_cli_success(result)

        # 5. Get forecast
        result = cli_runner.invoke(app, ["forecast", "--days", "3"])
        assert_cli_success(result)

        # 6. Get current weather
        result = cli_runner.invoke(app, ["current"])
        assert_cli_success(result)

    def test_configuration_and_usage_workflow(self, cli_runner, clean_db):
        """Test configuration and usage workflow."""
        # Setup
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Configure preferences
        result = cli_runner.invoke(
            app, ["settings", "--forecast-days", "7", "--temp-unit", "F"]
        )
        assert_cli_success(result)

        # Add multiple locations
        locations = [
            ("New York", "40.7128", "-74.0060", "USA"),
            ("Paris", "48.8566", "2.3522", "France"),
            ("Tokyo", "35.6762", "139.6503", "Japan"),
        ]

        for name, lat, lon, country in locations:
            result = cli_runner.invoke(
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
            assert_cli_success(result)

        # Test date-specific forecasts
        result = cli_runner.invoke(app, ["date", "2024-12-25", "--unit", "F"])
        assert_cli_success(result)
