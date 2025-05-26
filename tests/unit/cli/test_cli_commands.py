"""Tests for Typer CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from weather_app.cli import app


@pytest.fixture
def runner():
    """Create a CliRunner instance for testing."""
    return CliRunner()


@pytest.fixture
def mock_weather_app():
    """Mock WeatherApp instance."""
    with patch("weather_app.cli.WeatherApp") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_api():
    """Mock WeatherAPI instance."""
    with patch("weather_app.cli.WeatherAPI") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_display():
    """Mock WeatherDisplay instance."""
    with patch("weather_app.cli.WeatherDisplay") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


class TestVersionCommand:
    """Test the version command."""

    def test_version_command(self, runner):
        """Test version command returns correct output."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Weather Dashboard v0.1.0" in result.stdout


class TestInteractiveCommand:
    """Test the interactive command."""

    def test_interactive_command(self, runner, mock_weather_app):
        """Test interactive command calls run_from_user_input."""
        result = runner.invoke(app, ["interactive"])
        assert result.exit_code == 0
        mock_weather_app.run_from_user_input.assert_called_once()

    def test_interactive_command_with_verbose(self, runner, mock_weather_app):
        """Test interactive command with verbose flag."""
        result = runner.invoke(app, ["interactive", "--verbose"])
        assert result.exit_code == 0
        mock_weather_app.run_from_user_input.assert_called_once()


class TestCurrentCommand:
    """Test the current weather command."""

    def test_current_command_default(self, runner, mock_weather_app):
        """Test current command with default settings."""
        result = runner.invoke(app, ["current"])
        assert result.exit_code == 0
        mock_weather_app.run.assert_called_once()
        assert mock_weather_app.unit == "C"

    def test_current_command_fahrenheit(self, runner, mock_weather_app):
        """Test current command with Fahrenheit unit."""
        result = runner.invoke(app, ["current", "--unit", "F"])
        assert result.exit_code == 0
        mock_weather_app.run.assert_called_once()
        assert mock_weather_app.unit == "F"

    def test_current_command_verbose(self, runner, mock_weather_app):
        """Test current command with verbose flag."""
        result = runner.invoke(app, ["current", "--verbose"])
        assert result.exit_code == 0
        mock_weather_app.run.assert_called_once()


class TestForecastCommand:
    """Test the forecast command."""

    def test_forecast_command_default(self, runner, mock_weather_app):
        """Test forecast command with default settings."""
        result = runner.invoke(app, ["forecast"])
        assert result.exit_code == 0
        mock_weather_app.run.assert_called_once()
        assert mock_weather_app.unit == "C"

    def test_forecast_command_with_days(self, runner, mock_weather_app):
        """Test forecast command with specific days."""
        result = runner.invoke(app, ["forecast", "--days", "5"])
        assert result.exit_code == 0
        mock_weather_app.show_forecast_for_days.assert_called_once_with(5)
        assert mock_weather_app.unit == "C"

    def test_forecast_command_with_unit(self, runner, mock_weather_app):
        """Test forecast command with Fahrenheit unit."""
        result = runner.invoke(app, ["forecast", "--unit", "F", "--days", "3"])
        assert result.exit_code == 0
        mock_weather_app.show_forecast_for_days.assert_called_once_with(3)
        assert mock_weather_app.unit == "F"

    def test_forecast_command_invalid_days(self, runner):
        """Test forecast command with invalid days (out of range)."""
        result = runner.invoke(app, ["forecast", "--days", "10"])
        assert result.exit_code != 0  # Should fail validation


class TestWeatherCommand:
    """Test the weather command."""

    def test_weather_command_success(self, runner, mock_api, mock_display):
        """Test weather command with successful API response."""
        # Mock successful API response
        mock_weather_data = {
            "location": {"name": "London"},
            "current": {"temp_c": 15},
            "forecast": {"forecastday": []},
        }
        mock_api.get_weather.return_value = mock_weather_data

        result = runner.invoke(app, ["weather", "London"])
        assert result.exit_code == 0
        mock_api.get_weather.assert_called_once_with("London")
        mock_display.show_current_weather.assert_called_once_with(
            mock_weather_data, "C"
        )
        mock_display.show_forecast.assert_called_once_with(mock_weather_data, "C")

    def test_weather_command_fahrenheit(self, runner, mock_api, mock_display):
        """Test weather command with Fahrenheit unit."""
        mock_weather_data = {"location": {"name": "London"}}
        mock_api.get_weather.return_value = mock_weather_data

        result = runner.invoke(app, ["weather", "London", "--unit", "F"])
        assert result.exit_code == 0
        mock_display.show_current_weather.assert_called_once_with(
            mock_weather_data, "F"
        )
        mock_display.show_forecast.assert_called_once_with(mock_weather_data, "F")

    def test_weather_command_api_failure(self, runner, mock_api, mock_display):
        """Test weather command when API returns None."""
        mock_api.get_weather.return_value = None

        result = runner.invoke(app, ["weather", "London"])
        assert result.exit_code == 0
        assert "Failed to retrieve weather information" in result.stdout
        mock_display.show_current_weather.assert_not_called()
        mock_display.show_forecast.assert_not_called()

    def test_weather_command_missing_location(self, runner):
        """Test weather command without location argument."""
        result = runner.invoke(app, ["weather"])
        assert result.exit_code != 0  # Should fail due to missing required argument


class TestDateCommand:
    """Test the date forecast command."""

    def test_date_command_valid_date(self, runner, mock_weather_app):
        """Test date command with valid date format."""
        result = runner.invoke(app, ["date", "2024-12-25"])
        assert result.exit_code == 0
        mock_weather_app.show_forecast_for_date.assert_called_once()
        assert mock_weather_app.unit == "C"

    def test_date_command_with_unit(self, runner, mock_weather_app):
        """Test date command with Fahrenheit unit."""
        result = runner.invoke(app, ["date", "2024-12-25", "--unit", "F"])
        assert result.exit_code == 0
        mock_weather_app.show_forecast_for_date.assert_called_once()
        assert mock_weather_app.unit == "F"

    def test_date_command_invalid_date(self, runner):
        """Test date command with invalid date format."""
        result = runner.invoke(app, ["date", "invalid-date"])
        assert result.exit_code == 0  # Command runs but shows error message
        assert "Invalid date format" in result.stdout


class TestInitDbCommand:
    """Test the database initialization command."""

    def test_init_db_command_success(self, runner):
        """Test init-db command with successful initialization."""
        with patch("weather_app.cli.initialize_database") as mock_init:
            result = runner.invoke(app, ["init-db"])
            assert result.exit_code == 0
            mock_init.assert_called_once()
            assert "Database initialized successfully" in result.stdout

    def test_init_db_command_failure(self, runner):
        """Test init-db command with initialization failure."""
        with patch("weather_app.cli.initialize_database") as mock_init:
            mock_init.side_effect = Exception("Database error")
            result = runner.invoke(app, ["init-db"])
            assert result.exit_code == 0  # Command runs but shows error
            assert "Error initializing database" in result.stdout


class TestSetForecastDaysCommand:
    """Test the set forecast days command."""

    def test_set_forecast_days_valid(self, runner, mock_weather_app):
        """Test set forecast days with valid value."""
        result = runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert result.exit_code == 0
        mock_weather_app.set_default_forecast_days.assert_called_once_with(5)

    def test_set_forecast_days_invalid(self, runner):
        """Test set forecast days with invalid value."""
        result = runner.invoke(app, ["set-forecast-days", "--days", "10"])
        assert result.exit_code != 0  # Should fail validation


class TestSettingsCommand:
    """Test the settings command."""

    def test_settings_forecast_days(self, runner, mock_weather_app):
        """Test settings command with forecast days."""
        result = runner.invoke(app, ["settings", "--forecast-days", "7"])
        assert result.exit_code == 0
        mock_weather_app.set_default_forecast_days.assert_called_once_with(7)

    def test_settings_temp_unit(self, runner, mock_weather_app):
        """Test settings command with temperature unit."""
        with patch.object(mock_weather_app, "settings_repo") as mock_repo:
            result = runner.invoke(app, ["settings", "--temp-unit", "F"])
            assert result.exit_code == 0
            mock_repo.update_temperature_unit.assert_called_once_with("fahrenheit")

    def test_settings_both_options(self, runner, mock_weather_app):
        """Test settings command with both options."""
        with patch.object(mock_weather_app, "settings_repo") as mock_repo:
            result = runner.invoke(
                app, ["settings", "--forecast-days", "3", "--temp-unit", "C"]
            )
            assert result.exit_code == 0
            mock_weather_app.set_default_forecast_days.assert_called_once_with(3)
            mock_repo.update_temperature_unit.assert_called_once_with("celsius")


class TestAddLocationCommand:
    """Test the add location command."""

    def test_add_location_success(self, runner):
        """Test add location command with successful creation."""
        with patch("weather_app.cli.LocationRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_location = MagicMock()
            mock_location.name = "Paris"
            mock_location.country = "France"
            mock_location.region = "Île-de-France"
            mock_location.latitude = 48.8566
            mock_location.longitude = 2.3522
            mock_location.id = 1
            mock_repo.create.return_value = mock_location

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
                ],
            )
            assert result.exit_code == 0
            assert "Added location successfully" in result.stdout
            mock_repo.create.assert_called_once()

    def test_add_location_with_favorite(self, runner):
        """Test add location command with favorite flag."""
        with patch("weather_app.cli.LocationRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_location = MagicMock()
            mock_location.name = "Tokyo"
            mock_location.country = "Japan"
            mock_location.region = None
            mock_location.latitude = 35.6762
            mock_location.longitude = 139.6503
            mock_location.id = 2
            mock_repo.create.return_value = mock_location

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
                    "--favorite",
                ],
            )
            assert result.exit_code == 0
            assert "Added location successfully" in result.stdout


class TestHelpCommand:
    """Test help functionality."""

    def test_main_help(self, runner):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "A Totally Awesome Command-line Weather App" in result.stdout

    def test_command_help(self, runner):
        """Test help for specific command."""
        result = runner.invoke(app, ["weather", "--help"])
        assert result.exit_code == 0
        assert "Get current weather and forecast" in result.stdout


class TestCommandValidation:
    """Test command argument validation."""

    def test_unit_validation_case_insensitive(self, runner, mock_weather_app):
        """Test that unit validation is case insensitive."""
        result = runner.invoke(app, ["current", "--unit", "c"])
        assert result.exit_code == 0
        assert mock_weather_app.unit == "C"

        result = runner.invoke(app, ["current", "--unit", "f"])
        assert result.exit_code == 0
        assert mock_weather_app.unit == "F"

    def test_days_range_validation(self, runner):
        """Test that days parameter validates range correctly."""
        # Valid range
        result = runner.invoke(app, ["forecast", "--days", "1"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["forecast", "--days", "7"])
        assert result.exit_code == 0

        # Invalid range
        result = runner.invoke(app, ["forecast", "--days", "0"])
        assert result.exit_code != 0

        result = runner.invoke(app, ["forecast", "--days", "8"])
        assert result.exit_code != 0
