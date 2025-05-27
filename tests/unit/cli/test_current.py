"""Tests for the CurrentWeatherManager class."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from weather_app.current import CurrentWeatherManager
from weather_app.models import WeatherRecord


@pytest.fixture
def current_manager():
    """Create a CurrentWeatherManager instance with mocked dependencies."""
    with patch("weather_app.current.LocationRepository") as MockLocationRepo:
        with patch("weather_app.current.WeatherRepository") as MockWeatherRepo:
            with patch("weather_app.current.SettingsRepository") as MockSettingsRepo:
                # Create mocked instances
                mock_api = MagicMock()
                mock_display = MagicMock()
                mock_location_repo = MagicMock()
                mock_weather_repo = MagicMock()
                mock_settings_repo = MagicMock()

                # Configure constructor return values
                MockLocationRepo.return_value = mock_location_repo
                MockWeatherRepo.return_value = mock_weather_repo
                MockSettingsRepo.return_value = mock_settings_repo

                # Create manager
                manager = CurrentWeatherManager(mock_api, mock_display)

                # Store references for easy access
                manager._test_mocks = {
                    "api": mock_api,
                    "display": mock_display,
                    "location_repo": mock_location_repo,
                    "weather_repo": mock_weather_repo,
                    "settings_repo": mock_settings_repo,
                }

                # Configure settings repository with proper mock
                mock_settings = MagicMock()
                mock_settings.temperature_unit = "celsius"
                mock_settings.id = 1
                mock_settings_repo.get_settings.return_value = mock_settings

                return manager


def test_get_current_weather(current_manager, sample_location):
    """Test getting current weather for a location."""
    # Configure API response
    weather_data = {
        "location": {"name": sample_location.name, "country": sample_location.country},
        "current": {
            "temp_c": 20.5,
            "feelslike_c": 21.0,
            "humidity": 65,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            },
        },
    }
    current_manager.api.get_weather.return_value = weather_data

    # Call the method
    current_manager.get_current_weather(sample_location)

    # Check that API was called with correct parameters
    current_manager.api.get_weather.assert_called_with(
        f"{sample_location.latitude},{sample_location.longitude}"
    )

    # Check that weather record was saved
    assert current_manager.weather_repo.create.called

    # Check that display was called
    current_manager.display.show_current_weather.assert_called_with(weather_data, "C")


def test_get_current_weather_api_failure(current_manager, sample_location):
    """Test getting current weather with API failure."""
    # Configure API to return None (failure)
    current_manager.api.get_weather.return_value = None

    # Call the method
    current_manager.get_current_weather(sample_location)

    # Check that error was displayed
    current_manager.display.show_error.assert_called_once()

    # Check that nothing was saved
    assert not current_manager.weather_repo.create.called


def test_get_historical_weather(current_manager, sample_location):
    """Test getting historical weather for a location."""
    # Configure API response
    weather_data = {
        "location": {"name": sample_location.name, "country": sample_location.country},
        "forecast": {
            "forecastday": [
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "day": {
                        "avgtemp_c": 18.5,
                        "condition": {
                            "text": "Sunny",
                            "icon": (
                                "//cdn.weatherapi.com/weather/" "64x64/day/113.png"
                            ),
                        },
                    },
                }
            ]
        },
    }
    current_manager.api.get_weather.return_value = weather_data

    # Call the method
    current_manager.get_historical_weather(sample_location, days_back=1)

    # Check that API was called
    current_manager.api.get_weather.assert_called_once()

    # Check API parameters
    args, kwargs = current_manager.api.get_weather.call_args
    assert f"{sample_location.latitude},{sample_location.longitude}" in args
    assert "date" in kwargs

    # Check that display was called
    current_manager.display.show_historical_weather.assert_called_once()


def test_update_display_preferences_valid(current_manager):
    """Test updating display preferences with valid unit."""
    # Configure mock settings
    mock_settings = MagicMock()
    mock_settings.id = 1
    current_manager.settings_repo.get_settings.return_value = mock_settings

    # Call the method with valid unit
    current_manager.update_display_preferences("F")

    # Check that settings were updated
    current_manager.settings_repo.update_temperature_unit.assert_called_with(
        "fahrenheit"
    )

    # Check that message was displayed
    current_manager.display.show_message.assert_called_once()


def test_update_display_preferences_invalid(current_manager):
    """Test updating display preferences with invalid unit."""
    # Call the method with invalid unit
    current_manager.update_display_preferences("K")  # Kelvin not supported

    # Check that error was displayed
    current_manager.display.show_error.assert_called_once()

    # Check that settings were not updated
    assert not current_manager.settings_repo.update_temperature_unit.called


def test_save_weather_record(current_manager, sample_location):
    """Test saving a weather record to the database."""
    # Create weather data
    weather_data = {
        "current": {
            "temp_c": 22.0,
            "feelslike_c": 23.5,
            "humidity": 70,
            "pressure_mb": 1015,
            "wind_kph": 15.0,
            "wind_dir": "NW",
            "condition": {
                "text": "Clear",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
            },
        }
    }

    # Configure repo to return a record on create
    mock_record = MagicMock(spec=WeatherRecord)
    current_manager.weather_repo.create.return_value = mock_record

    # Call the method
    result = current_manager._save_weather_record(sample_location, weather_data)

    # Check that repo was called
    assert current_manager.weather_repo.create.called

    # Check the result
    assert result == mock_record

    # Verify that created record has correct data
    created_record = current_manager.weather_repo.create.call_args[0][0]
    assert created_record.location_id == sample_location.id
    assert created_record.temperature == 22.0
    assert created_record.feels_like == 23.5
    assert created_record.humidity == 70
    assert created_record.condition == "Clear"
