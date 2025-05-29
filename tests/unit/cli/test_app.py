"""Tests for the WeatherApp class."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from weather_app.cli_app import WeatherApp


@pytest.fixture
def mock_user_input():
    """Create a mocked User_Input_Information class."""
    with patch("weather_app.cli_app.User_Input_Information") as mock_class:
        # Configure method return values
        mock_class.get_temperature_choice.return_value = "1"  # Celsius
        yield mock_class


@pytest.fixture
def app():
    """Create a WeatherApp instance with mocked dependencies."""
    with patch("weather_app.cli_app.Database") as MockDatabase:
        with patch("weather_app.cli_app.WeatherAPI") as MockWeatherAPI:
            with patch("weather_app.cli_app.WeatherDisplay") as MockDisplay:
                with patch("weather_app.cli_app.LocationManager") as MockLM:
                    with patch("weather_app.cli_app.ForecastManager") as MockFM:
                        with patch(
                            "weather_app.cli_app.CurrentWeatherManager"
                        ) as MockCM:
                            with patch(
                                "weather_app.cli_app.LocationRepository"
                            ) as MockLR:
                                with patch(
                                    "weather_app.cli_app.SettingsRepository"
                                ) as MockSR:
                                    # Create mocked instances
                                    mock_database = MagicMock()
                                    mock_api = MagicMock()
                                    mock_display = MagicMock()
                                    mock_location_manager = MagicMock()
                                    mock_forecast_manager = MagicMock()
                                    mock_current_manager = MagicMock()
                                    mock_location_repo = MagicMock()
                                    mock_settings_repo = MagicMock()

                                    # Configure constructor return values
                                    MockDatabase.return_value = mock_database
                                    MockWeatherAPI.return_value = mock_api
                                    MockDisplay.return_value = mock_display
                                    MockLM.return_value = mock_location_manager
                                    MockFM.return_value = mock_forecast_manager
                                    MockCM.return_value = mock_current_manager
                                    MockLR.return_value = mock_location_repo
                                    MockSR.return_value = mock_settings_repo

                                    # Create app with all dependencies mocked
                                    app = WeatherApp()

                                    # Store references to mocks for easy
                                    # access in tests
                                    app._test_mocks = {
                                        "database": mock_database,
                                        "api": mock_api,
                                        "display": mock_display,
                                        "location_manager": (mock_location_manager),
                                        "forecast_manager": (mock_forecast_manager),
                                        "current_manager": (mock_current_manager),
                                        "location_repo": mock_location_repo,
                                        "settings_repo": mock_settings_repo,
                                    }

                                    return app


def test_run_success(app, sample_location):
    """Test the run method with successful execution."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo
    current_manager = app.current_manager
    forecast_manager = app.forecast_manager

    # Configure location manager
    location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    location_repo.find_by_coordinates.return_value = sample_location
    location_repo.find_or_create_by_coordinates.return_value = sample_location

    # Call the method
    app.run()

    # Check that the correct methods were called
    assert location_manager.get_location.called
    assert location_repo.find_by_coordinates.called
    assert current_manager.get_current_weather.called
    assert forecast_manager.get_forecast.called


def test_run_no_location(app):
    """Test the run method with no location selected."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo

    # Configure location manager to return None
    location_manager.get_location.return_value = None

    # Call the method
    app.run()

    # Check that only the location manager was called
    assert location_manager.get_location.called
    assert not location_repo.find_by_coordinates.called


def test_run_from_user_input_success(app, sample_location, mock_user_input):
    """Test the run_from_user_input method with successful execution."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo
    current_manager = app.current_manager
    forecast_manager = app.forecast_manager

    # Configure location manager
    location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    location_repo.find_by_coordinates.return_value = sample_location
    location_repo.find_or_create_by_coordinates.return_value = sample_location

    # Configure user input
    app.user_input = mock_user_input
    app.user_input.get_temperature_choice.return_value = "1"  # Celsius

    # Call the method
    app.run_from_user_input()

    # Check that the correct methods were called
    assert app.user_input.get_temperature_choice.called
    assert location_manager.get_location.called
    assert location_repo.find_by_coordinates.called
    assert current_manager.get_current_weather.called
    assert forecast_manager.get_forecast.called


def test_run_from_user_input_no_location(app, mock_user_input):
    """Test the run_from_user_input method with no location selected."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo

    # Configure location manager to return None
    location_manager.get_location.return_value = None

    # Configure user input
    app.user_input = mock_user_input

    # Call the method
    app.run_from_user_input()

    # Check that only the user input and location manager were called
    assert app.user_input.get_temperature_choice.called
    assert location_manager.get_location.called
    assert not location_repo.find_by_coordinates.called


def test_show_forecast_for_days(app, sample_location):
    """Test the show_forecast_for_days method."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo
    forecast_manager = app.forecast_manager

    # Configure location manager
    location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    location_repo.find_by_coordinates.return_value = sample_location
    location_repo.find_or_create_by_coordinates.return_value = sample_location

    # Call the method
    app.show_forecast_for_days(3)

    # Check that the correct methods were called
    assert location_manager.get_location.called
    assert location_repo.find_by_coordinates.called
    assert forecast_manager.get_forecast.called
    # The location passed will be from find_or_create_by_coordinates,
    # not the original sample_location
    forecast_manager.get_forecast.assert_called()


def test_show_forecast_for_date(app, sample_location):
    """Test the show_forecast_for_date method."""
    # Get the mocks
    location_manager = app.location_manager
    location_repo = app.location_repo
    forecast_manager = app.forecast_manager

    # Configure location manager
    location_manager.get_location.return_value = "51.52,-0.11"

    # Configure location repository
    location_repo.find_by_coordinates.return_value = sample_location
    location_repo.find_or_create_by_coordinates.return_value = sample_location

    # Mock date
    test_date = datetime(2023, 5, 7)

    # Call the method
    app.show_forecast_for_date(test_date)

    # Check that the correct methods were called
    assert location_manager.get_location.called
    assert location_repo.find_by_coordinates.called
    assert forecast_manager.get_forecast_for_day.called
    # The location passed will be from find_or_create_by_coordinates,
    # not the original sample_location
    forecast_manager.get_forecast_for_day.assert_called()


def test_set_default_forecast_days(app):
    """Test the set_default_forecast_days method."""
    # Get the mocks
    forecast_manager = app.forecast_manager

    # Call the method
    app.set_default_forecast_days(5)

    # Check that the forecast manager was called
    assert forecast_manager.update_forecast_days.called
    forecast_manager.update_forecast_days.assert_called_with(5)
