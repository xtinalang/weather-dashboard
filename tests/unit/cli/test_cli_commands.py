"""Tests for Typer CLI commands with type hints and flattened code structure."""

from typing import Any, Dict, Generator, List, Union
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner, Result

from weather_app.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CliRunner instance for testing."""
    return CliRunner()


@pytest.fixture
def mock_weather_app() -> Generator[MagicMock, None, None]:
    """Mock WeatherApp instance."""
    with patch("weather_app.cli.WeatherApp") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_api() -> Generator[MagicMock, None, None]:
    """Mock WeatherAPI instance."""
    with patch("weather_app.cli.WeatherAPI") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_display() -> Generator[MagicMock, None, None]:
    """Mock WeatherDisplay instance."""
    with patch("weather_app.cli.WeatherDisplay") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


# Version Command Tests
def test_version_command(runner: CliRunner) -> None:
    """Test version command returns correct output."""
    result: Result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Weather Dashboard v0.1.0" in result.stdout


# Interactive Command Tests
def test_interactive_command(runner: CliRunner, mock_weather_app: MagicMock) -> None:
    """Test interactive command calls run_from_user_input."""
    result: Result = runner.invoke(app, ["interactive"])
    assert result.exit_code == 0
    mock_weather_app.run_from_user_input.assert_called_once()


def test_interactive_command_with_verbose(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test interactive command with verbose flag."""
    result: Result = runner.invoke(app, ["interactive", "--verbose"])
    assert result.exit_code == 0
    mock_weather_app.run_from_user_input.assert_called_once()


# Current Command Tests
def test_current_command_default(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test current command with default settings."""
    result: Result = runner.invoke(app, ["current"])
    assert result.exit_code == 0
    mock_weather_app.run.assert_called_once()
    assert mock_weather_app.unit == "C"


def test_current_command_fahrenheit(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test current command with Fahrenheit unit."""
    result: Result = runner.invoke(app, ["current", "--unit", "F"])
    assert result.exit_code == 0
    mock_weather_app.run.assert_called_once()
    assert mock_weather_app.unit == "F"


def test_current_command_verbose(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test current command with verbose flag."""
    result: Result = runner.invoke(app, ["current", "--verbose"])
    assert result.exit_code == 0
    mock_weather_app.run.assert_called_once()


# Forecast Command Tests
def test_forecast_command_default(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test forecast command with default settings."""
    result: Result = runner.invoke(app, ["forecast"])
    assert result.exit_code == 0
    mock_weather_app.run.assert_called_once()
    assert mock_weather_app.unit == "C"


def test_forecast_command_with_days(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test forecast command with specific days."""
    result: Result = runner.invoke(app, ["forecast", "--days", "5"])
    assert result.exit_code == 0
    mock_weather_app.show_forecast_for_days.assert_called_once_with(5)
    assert mock_weather_app.unit == "C"


def test_forecast_command_with_unit(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test forecast command with Fahrenheit unit."""
    result: Result = runner.invoke(app, ["forecast", "--unit", "F", "--days", "3"])
    assert result.exit_code == 0
    mock_weather_app.show_forecast_for_days.assert_called_once_with(3)
    assert mock_weather_app.unit == "F"


def test_forecast_command_invalid_days(runner: CliRunner) -> None:
    """Test forecast command with invalid days (out of range)."""
    result: Result = runner.invoke(app, ["forecast", "--days", "10"])
    assert result.exit_code != 0  # Should fail validation


# Weather Command Tests
def test_weather_command_success(
    runner: CliRunner, mock_api: MagicMock, mock_display: MagicMock
) -> None:
    """Test weather command with successful API response."""
    mock_weather_data: Dict[str, Any] = {
        "location": {"name": "London"},
        "current": {"temp_c": 15},
        "forecast": {"forecastday": []},
    }
    mock_api.get_weather.return_value = mock_weather_data

    result: Result = runner.invoke(app, ["weather", "London"])
    assert result.exit_code == 0
    mock_api.get_weather.assert_called_once_with("London")
    mock_display.show_current_weather.assert_called_once_with(mock_weather_data, "C")
    mock_display.show_forecast.assert_called_once_with(mock_weather_data, "C")


def test_weather_command_fahrenheit(
    runner: CliRunner, mock_api: MagicMock, mock_display: MagicMock
) -> None:
    """Test weather command with Fahrenheit unit."""
    mock_weather_data: Dict[str, Any] = {"location": {"name": "London"}}
    mock_api.get_weather.return_value = mock_weather_data

    result: Result = runner.invoke(app, ["weather", "London", "--unit", "F"])
    assert result.exit_code == 0
    mock_display.show_current_weather.assert_called_once_with(mock_weather_data, "F")
    mock_display.show_forecast.assert_called_once_with(mock_weather_data, "F")


def test_weather_command_api_failure(
    runner: CliRunner, mock_api: MagicMock, mock_display: MagicMock
) -> None:
    """Test weather command when API returns None."""
    mock_api.get_weather.return_value = None

    result: Result = runner.invoke(app, ["weather", "London"])
    assert result.exit_code == 0
    assert "Failed to retrieve weather information" in result.stdout
    mock_display.show_current_weather.assert_not_called()
    mock_display.show_forecast.assert_not_called()


def test_weather_command_missing_location(runner: CliRunner) -> None:
    """Test weather command without location argument."""
    result: Result = runner.invoke(app, ["weather"])
    assert result.exit_code != 0  # Should fail due to missing required argument


# Date Command Tests
def test_date_command_valid_date(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test date command with valid date format."""
    result: Result = runner.invoke(app, ["date", "2024-12-25"])
    assert result.exit_code == 0
    mock_weather_app.show_forecast_for_date.assert_called_once()
    assert mock_weather_app.unit == "C"


def test_date_command_with_unit(runner: CliRunner, mock_weather_app: MagicMock) -> None:
    """Test date command with Fahrenheit unit."""
    result: Result = runner.invoke(app, ["date", "2024-12-25", "--unit", "F"])
    assert result.exit_code == 0
    mock_weather_app.show_forecast_for_date.assert_called_once()
    assert mock_weather_app.unit == "F"


def test_date_command_invalid_date(runner: CliRunner) -> None:
    """Test date command with invalid date format."""
    result: Result = runner.invoke(app, ["date", "invalid-date"])
    assert result.exit_code == 0  # Command runs but shows error message
    assert "Invalid date format" in result.stdout


# Database Initialization Command Tests
def test_init_db_command_success(runner: CliRunner) -> None:
    """Test init-db command with successful initialization."""
    with patch("weather_app.cli.initialize_database") as mock_init:
        result: Result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0
        mock_init.assert_called_once()
        assert "Database initialized successfully" in result.stdout


def test_init_db_command_failure(runner: CliRunner) -> None:
    """Test init-db command with initialization failure."""
    with patch("weather_app.cli.initialize_database") as mock_init:
        mock_init.side_effect = Exception("Database error")
        result: Result = runner.invoke(app, ["init-db"])
        assert result.exit_code == 0  # Command runs but shows error
        assert "Error initializing database" in result.stdout


# Set Forecast Days Command Tests
def test_set_forecast_days_valid(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test set forecast days with valid value."""
    result: Result = runner.invoke(app, ["set-forecast-days", "--days", "5"])
    assert result.exit_code == 0
    mock_weather_app.set_default_forecast_days.assert_called_once_with(5)


def test_set_forecast_days_invalid(runner: CliRunner) -> None:
    """Test set forecast days with invalid value."""
    result: Result = runner.invoke(app, ["set-forecast-days", "--days", "10"])
    assert result.exit_code != 0  # Should fail validation


# Settings Command Tests
def test_settings_forecast_days(runner: CliRunner, mock_weather_app: MagicMock) -> None:
    """Test settings command with forecast days."""
    result: Result = runner.invoke(app, ["settings", "--forecast-days", "7"])
    assert result.exit_code == 0
    mock_weather_app.set_default_forecast_days.assert_called_once_with(7)


def test_settings_temp_unit(runner: CliRunner, mock_weather_app: MagicMock) -> None:
    """Test settings command with temperature unit."""
    with patch.object(mock_weather_app, "settings_repo") as mock_repo:
        result: Result = runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert result.exit_code == 0
        mock_repo.update_temperature_unit.assert_called_once_with("fahrenheit")


def test_settings_both_options(runner: CliRunner, mock_weather_app: MagicMock) -> None:
    """Test settings command with both options."""
    with patch.object(mock_weather_app, "settings_repo") as mock_repo:
        result: Result = runner.invoke(
            app, ["settings", "--forecast-days", "3", "--temp-unit", "C"]
        )
        assert result.exit_code == 0
        mock_weather_app.set_default_forecast_days.assert_called_once_with(3)
        mock_repo.update_temperature_unit.assert_called_once_with("celsius")


# Add Location Command Tests
def test_add_location_success(runner: CliRunner) -> None:
    """Test add location command with successful creation."""
    with patch("weather_app.cli.LocationRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_location = _create_mock_location(
            name="Paris",
            country="France",
            region="Île-de-France",
            latitude=48.8566,
            longitude=2.3522,
            location_id=1,
        )
        mock_repo.create.return_value = mock_location

        cmd_args: List[str] = [
            "add-location",
            "--name",
            "Paris",
            "--lat",
            "48.8566",
            "--lon",
            "2.3522",
            "--country",
            "France",
        ]
        result: Result = runner.invoke(app, cmd_args)

        assert result.exit_code == 0
        assert "Added location successfully" in result.stdout
        mock_repo.create.assert_called_once()


def test_add_location_with_favorite(runner: CliRunner) -> None:
    """Test add location command with favorite flag."""
    with patch("weather_app.cli.LocationRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_location = _create_mock_location(
            name="Tokyo",
            country="Japan",
            region=None,
            latitude=35.6762,
            longitude=139.6503,
            location_id=2,
        )
        mock_repo.create.return_value = mock_location

        cmd_args: List[str] = [
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
        ]
        result: Result = runner.invoke(app, cmd_args)

        assert result.exit_code == 0
        assert "Added location successfully" in result.stdout


# Help Command Tests
def test_main_help(runner: CliRunner) -> None:
    """Test main help command."""
    result: Result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A Totally Awesome Command-line Weather App" in result.stdout


def test_command_help(runner: CliRunner) -> None:
    """Test help for specific command."""
    result: Result = runner.invoke(app, ["weather", "--help"])
    assert result.exit_code == 0
    assert "Get current weather and forecast" in result.stdout


# Command Validation Tests
def test_unit_validation_case_insensitive(
    runner: CliRunner, mock_weather_app: MagicMock
) -> None:
    """Test that unit validation is case insensitive."""
    # Test lowercase celsius
    result: Result = runner.invoke(app, ["current", "--unit", "c"])
    assert result.exit_code == 0
    assert mock_weather_app.unit == "C"

    # Test lowercase fahrenheit
    result = runner.invoke(app, ["current", "--unit", "f"])
    assert result.exit_code == 0
    assert mock_weather_app.unit == "F"


def test_days_range_validation(runner: CliRunner) -> None:
    """Test that days parameter validates range correctly."""
    # Test valid range minimum
    result: Result = runner.invoke(app, ["forecast", "--days", "1"])
    assert result.exit_code == 0

    # Test valid range maximum
    result = runner.invoke(app, ["forecast", "--days", "7"])
    assert result.exit_code == 0

    # Test invalid range below minimum
    result = runner.invoke(app, ["forecast", "--days", "0"])
    assert result.exit_code != 0

    # Test invalid range above maximum
    result = runner.invoke(app, ["forecast", "--days", "8"])
    assert result.exit_code != 0


# Helper Functions
def _create_mock_location(
    name: str,
    country: str,
    latitude: float,
    longitude: float,
    location_id: int,
    region: Union[str, None] = None,
) -> MagicMock:
    """Create a mock location object with specified attributes."""
    mock_location = MagicMock()
    mock_location.name = name
    mock_location.country = country
    mock_location.region = region
    mock_location.latitude = latitude
    mock_location.longitude = longitude
    mock_location.id = location_id
    return mock_location
