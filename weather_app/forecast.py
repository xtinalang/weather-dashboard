from datetime import datetime
from typing import Any, cast

from .api import WeatherAPI
from .display import WeatherDisplay
from .models import Location, UserSettings
from .repository import LocationRepository, SettingsRepository
from .weather_types import ForecastData, ForecastDay, TemperatureUnit, WeatherResponse


class ForecastManager:
    def __init__(self, api: WeatherAPI, display: WeatherDisplay) -> None:
        self.api: WeatherAPI = api
        self.display: WeatherDisplay = display
        self.location_repo: LocationRepository = LocationRepository()
        self.settings_repo: SettingsRepository = SettingsRepository()

    def get_forecast(
        self,
        location: Location,
        days: int | None = None,
        unit: TemperatureUnit | None = None,
    ) -> None:
        try:
            # Use user's preferred forecast days from settings if not specified
            forecast_days: int
            if days is None:
                try:
                    settings: UserSettings = self.settings_repo.get_settings()
                    forecast_days = settings.forecast_days
                except Exception as e:
                    self.display.show_warning(
                        f"Error getting forecast days setting: {e}"
                    )
                    forecast_days = 7  # Default if settings fail
            else:
                forecast_days = days

            # Use user's preferred temperature unit if not specified
            temp_unit: TemperatureUnit
            if unit is None:
                try:
                    user_settings: UserSettings = self.settings_repo.get_settings()
                    temp_unit = cast(
                        TemperatureUnit,
                        "F"
                        if user_settings.temperature_unit.lower() == "fahrenheit"
                        else "C",
                    )
                except Exception as e:
                    self.display.show_warning(
                        f"Error getting temperature unit setting: {e}"
                    )
                    temp_unit = "C"  # Default if settings fail
            else:
                temp_unit = unit

            # Ensure days is within valid range (usually 1-7 for free API tiers)
            forecast_days = max(1, min(forecast_days, 7))

            # Get forecast data from API
            coords: str = f"{location.latitude},{location.longitude}"
            forecast_data: WeatherResponse | None = self.api.get_forecast(
                coords, days=forecast_days
            )

            if not forecast_data:
                self.display.show_error(f"Failed to get forecast for {location.name}")
                return

            # Display the forecast
            self.display.show_forecast(
                cast(dict[str, Any], forecast_data), unit=temp_unit, days=forecast_days
            )
        except Exception as e:
            self.display.show_error(f"Error getting forecast: {e}")

    def get_forecast_for_day(
        self,
        location: Location,
        target_date: datetime,
        unit: TemperatureUnit | None = None,
    ) -> None:
        try:
            # Use user's preferred temperature unit if not specified
            temp_unit: TemperatureUnit
            if unit is None:
                settings: UserSettings = self.settings_repo.get_settings()
                temp_unit = cast(
                    TemperatureUnit,
                    "F" if settings.temperature_unit.lower() == "fahrenheit" else "C",
                )
            else:
                temp_unit = unit

            # Calculate how many days in the future the target date is
            days_ahead: int = (target_date.date() - datetime.now().date()).days

            # Check if the date is within the forecast range (usually 1-7 days)
            if days_ahead < 0:
                self.display.show_error("Cannot forecast for past dates")
                return
            if days_ahead > 7:
                self.display.show_error("Cannot forecast more than 7 days ahead")
                return

            # Get forecast data
            coords: str = f"{location.latitude},{location.longitude}"
            forecast_data: WeatherResponse | None = self.api.get_forecast(
                coords,
                days=days_ahead + 1,  # +1 because we need to include the target day
            )

            if not forecast_data:
                self.display.show_error(f"Failed to get forecast for {location.name}")
                return

            # Filter for the specific day and display
            target_forecast: ForecastDay | None = self._filter_forecast_for_date(
                forecast_data, target_date
            )
            if target_forecast:
                single_day_forecast: ForecastData = {
                    "forecast": {"forecastday": [target_forecast]}
                }
                self.display.show_forecast(
                    cast(dict[str, Any], single_day_forecast), unit=temp_unit
                )
            else:
                self.display.show_error(
                    f"No forecast available for {target_date.date()}"
                )
        except Exception as e:
            self.display.show_error(f"Error getting forecast for date: {e}")

    def _filter_forecast_for_date(
        self, forecast_data: WeatherResponse, target_date: datetime
    ) -> ForecastDay | None:
        target_date_str: str = target_date.date().isoformat()

        forecast_list = forecast_data.get("forecast", {}).get("forecastday", [])
        for day in cast(list[dict[str, Any]], forecast_list):
            if day.get("date") == target_date_str:
                return cast(ForecastDay, day)
        return None

    def update_forecast_days(self, days: int) -> None:
        try:
            # Ensure days is within valid range
            valid_days: int = max(1, min(days, 7))

            # Update settings
            settings: UserSettings = self.settings_repo.get_settings()
            self.settings_repo.update(settings.id, {"forecast_days": valid_days})

            self.display.show_message(f"Default forecast days updated to {valid_days}")
        except Exception as e:
            self.display.show_error(f"Failed to update forecast days: {e}")
