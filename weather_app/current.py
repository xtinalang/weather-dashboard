"""
Current weather management module.
Handles retrieving, processing, and displaying current weather data.
"""

import logging
from datetime import datetime, timedelta
from typing import cast

from .api import WeatherAPI
from .display import WeatherDisplay
from .models import Location, UserSettings, WeatherRecord
from .repository import LocationRepository, SettingsRepository, WeatherRepository
from .weather_types import (
    CurrentWeather,
    TemperatureUnit,
    WeatherCondition,
    WeatherData,
)

logger = logging.getLogger(__name__)


class CurrentWeatherManager:
    """
    Manager for current weather operations.
    Retrieves current weather from API, saves to database, and handles display.
    """

    def __init__(self, api: WeatherAPI, display: WeatherDisplay) -> None:
        """Initialize the CurrentWeatherManager with API and display components."""
        self.api: WeatherAPI = api
        self.display: WeatherDisplay = display
        self.location_repo: LocationRepository = LocationRepository()
        self.weather_repo: WeatherRepository = WeatherRepository()
        self.settings_repo: SettingsRepository = SettingsRepository()

    def get_current_weather(self, location: Location) -> None:
        try:
            # Get user settings for temperature unit
            temp_unit: TemperatureUnit
            try:
                settings: UserSettings = self.settings_repo.get_settings()
                temp_unit = cast(
                    TemperatureUnit,
                    "F" if settings.temperature_unit.lower() == "fahrenheit" else "C",
                )
            except Exception as e:
                self.display.show_warning(
                    f"Error getting temperature unit setting: {e}"
                )
                temp_unit = "C"  # Default if settings fail

            # Get weather data from API
            coords: str = f"{location.latitude},{location.longitude}"
            weather_data: WeatherData | None = cast(
                WeatherData | None, self.api.get_weather(coords)
            )

            if not weather_data:
                self.display.show_error(
                    f"Failed to get current weather for {location.name}"
                )
                return

            # Save weather data to database
            try:
                saved_record: WeatherRecord | None = self._save_weather_record(
                    location, weather_data
                )
                if saved_record:
                    logger.debug(f"Saved weather record with ID: {saved_record.id}")
            except Exception as e:
                self.display.show_warning(f"Failed to save weather data: {e}")
                # Continue anyway to show the weather

            # Display the current weather
            self.display.show_current_weather(weather_data, temp_unit)
        except Exception as e:
            self.display.show_error(f"Error retrieving current weather: {e}")

    def get_historical_weather(self, location: Location, days_back: int = 1) -> None:
        # Ensure days_back is within valid range (API usually limits to 7 days)
        valid_days_back: int = max(1, min(days_back, 7))

        # Calculate the historical date
        historical_date: datetime = datetime.now() - timedelta(days=valid_days_back)
        date_str: str = historical_date.strftime("%Y-%m-%d")

        # Get historical weather data from API
        coords: str = f"{location.latitude},{location.longitude}"
        weather_data: WeatherData | None = cast(
            WeatherData | None, self.api.get_weather(coords, date=date_str)
        )

        if not weather_data:
            self.display.show_error(
                f"Failed to get historical weather for {location.name}"
            )
            return

        # Display the historical weather
        self.display.show_historical_weather(weather_data, date_str)

    def update_display_preferences(self, temperature_unit: str) -> None:
        try:
            # Validate unit value
            valid_unit: str = temperature_unit.upper()
            if valid_unit not in ["C", "F"]:
                self.display.show_error("Invalid temperature unit. Use 'C' or 'F'.")
                return

            # Determine full unit name
            unit_value: str = "celsius" if valid_unit == "C" else "fahrenheit"

            # Update settings directly using the update_temperature_unit method
            try:
                self.settings_repo.update_temperature_unit(unit_value)
                self.display.show_message(f"Temperature unit updated to {unit_value}")
                logger.info(f"Temperature unit updated to {unit_value}")
            except Exception as e:
                self.display.show_error(
                    f"Failed to update temperature unit in database: {e}"
                )

        except Exception as e:
            self.display.show_error(f"Failed to update temperature unit: {e}")

    def _save_weather_record(
        self, location: Location, weather_data: WeatherData
    ) -> WeatherRecord | None:
        try:
            # Extract current weather from API response
            current: CurrentWeather = weather_data.get("current", {})
            condition_obj: WeatherCondition = current.get("condition", {})

            # Create WeatherRecord object
            record: WeatherRecord = WeatherRecord(
                location_id=location.id,
                timestamp=datetime.now(),
                temperature=current.get("temp_c", 0.0),
                feels_like=current.get("feelslike_c", 0.0),
                humidity=current.get("humidity", 0),
                pressure=current.get("pressure_mb", 0.0),
                wind_speed=current.get("wind_kph", 0.0),
                wind_direction=current.get("wind_dir", ""),
                condition=condition_obj.get("text", "Unknown"),
                condition_description=condition_obj.get("text", "Unknown"),
            )

            return self.weather_repo.create(record)
        except Exception as e:
            self.display.show_error(f"Failed to save weather data: {e}")
            return None

    def get_latest_weather(self, location: Location) -> WeatherRecord | None:
        try:
            record: WeatherRecord | None = self.weather_repo.get_latest_for_location(
                location.id
            )
            if record:
                logger.info(f"Found latest weather record for {location.name}")
                return record
            else:
                logger.info(f"No weather records found for {location.name}")
                return None
        except Exception as e:
            logger.error(f"Error getting latest weather: {e}")
            return None
