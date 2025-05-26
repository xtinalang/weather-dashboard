"""Tests for the WeatherApp class."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from weather_app.cli_app import WeatherApp


@pytest.fixture
def mock_user_input():
    """Create a mocked User_Input_Information class."""
    with patch("weather_app.app.User_Input_Information") as mock_class:
        # Configure method return values
        mock_class.get_temperature_choice.return_value = "1"  # Celsius
        yield mock_class


@pytest.fixture
def app(mock_database, mock_api, mock_display, mock_location_repo, mock_settings_repo):
    """Create a WeatherApp instance with mocked dependencies."""
    with patch("weather_app.app.LocationManager") as MockLocationManager:
        with patch("weather_app.app.ForecastManager") as MockForecastManager:
            # Create mocked instances
            mock_location_manager = MagicMock()
            mock_forecast_manager = MagicMock()

            # Configure return values
            MockLocationManager.return_value = mock_location_manager
            MockForecastManager.return_value = mock_forecast_manager

            # Create app
            app = WeatherApp()

            # Replace with mocks
            app.db = mock_database
            app.weather_api = mock_api
            app.display = mock_display
            app.location_manager = mock_location_manager
            app.forecast_manager = mock_forecast_manager
            app.location_repo = mock_location_repo
            app.settings_repo = mock_settings_repo

            return app


def test_run_success(app, sample_location):
    """Test the run method with successful execution."""
    # Configure location manager
    app.location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    app.location_repo.find_by_coordinates.return_value = sample_location
    app.location_repo.get_by_id.return_value = sample_location

    # Configure settings repository
    app.settings_repo.get_settings.return_value = MagicMock()

    # Call the method
    app.run()

    # Check that the correct methods were called
    assert app.location_manager.get_location.called
    assert app.location_repo.find_by_coordinates.called
    assert app.location_repo.get_by_id.called
    assert app.weather_api.get_weather.called
    assert app.display.show_weather.called
    assert app.settings_repo.get_settings.called
    assert app.forecast_manager.get_forecast.called


def test_run_no_location(app):
    """Test the run method with no location selected."""
    # Configure location manager to return None
    app.location_manager.get_location.return_value = None

    # Call the method
    app.run()

    # Check that only the location manager was called
    assert app.location_manager.get_location.called
    assert not app.location_repo.find_by_coordinates.called
    assert not app.weather_api.get_weather.called
    assert not app.display.show_weather.called
    assert not app.forecast_manager.get_forecast.called


def test_run_from_user_input_success(app, sample_location, mock_user_input):
    """Test the run_from_user_input method with successful execution."""
    # Configure location manager
    app.location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    app.location_repo.find_by_coordinates.return_value = sample_location
    app.location_repo.get_by_id.return_value = sample_location

    # Configure user input
    app.user_input = mock_user_input
    app.user_input.get_temperature_choice.return_value = "1"  # Celsius

    # Call the method
    app.run_from_user_input()

    # Check that the correct methods were called
    assert app.user_input.get_temperature_choice.called
    assert app.location_manager.get_location.called
    assert app.location_repo.find_by_coordinates.called
    assert app.location_repo.get_by_id.called
    assert app.weather_api.get_weather.called
    assert app.display.show_current_weather.called
    assert app.display.show_forecast.called


def test_run_from_user_input_no_location(app, mock_user_input):
    """Test the run_from_user_input method with no location selected."""
    # Configure location manager to return None
    app.location_manager.get_location.return_value = None

    # Configure user input
    app.user_input = mock_user_input

    # Call the method
    app.run_from_user_input()

    # Check that only the user input and location manager were called
    assert app.user_input.get_temperature_choice.called
    assert app.location_manager.get_location.called
    assert not app.location_repo.find_by_coordinates.called
    assert not app.weather_api.get_weather.called
    assert not app.display.show_current_weather.called
    assert not app.display.show_forecast.called


def test_show_forecast_for_days(app, sample_location):
    """Test the show_forecast_for_days method."""
    # Configure location manager
    app.location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    app.location_repo.find_by_coordinates.return_value = sample_location
    app.location_repo.get_by_id.return_value = sample_location

    # Call the method
    app.show_forecast_for_days(3)

    # Check that the correct methods were called
    assert app.location_manager.get_location.called
    assert app.location_repo.find_by_coordinates.called
    assert app.location_repo.get_by_id.called
    assert app.forecast_manager.get_forecast.called
    app.forecast_manager.get_forecast.assert_called_with(sample_location, days=3)


def test_show_forecast_for_date(app, sample_location):
    """Test the show_forecast_for_date method."""
    # Configure location manager
    app.location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    app.location_repo.find_by_coordinates.return_value = sample_location
    app.location_repo.get_by_id.return_value = sample_location

    # Mock date
    test_date = datetime(2023, 5, 7)

    # Call the method
    app.show_forecast_for_date(test_date)

    # Check that the correct methods were called
    assert app.location_manager.get_location.called
    assert app.location_repo.find_by_coordinates.called
    assert app.location_repo.get_by_id.called
    assert app.forecast_manager.get_forecast_for_day.called
    app.forecast_manager.get_forecast_for_day.assert_called_with(
        sample_location, test_date
    )


def test_set_default_forecast_days(app):
    """Test the set_default_forecast_days method."""
    # Call the method
    app.set_default_forecast_days(5)

    # Check that the forecast manager was called
    assert app.forecast_manager.update_forecast_days.called
    app.forecast_manager.update_forecast_days.assert_called_with(5)
