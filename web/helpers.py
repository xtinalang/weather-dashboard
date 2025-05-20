from typing import Any, Dict, Optional, Tuple

from flask import flash, redirect, render_template, request, url_for

from weather_app.api import WeatherAPI
from weather_app.app import WeatherApp
from weather_app.current import CurrentWeatherManager
from weather_app.display import WeatherDisplay
from weather_app.forecast import ForecastManager
from weather_app.location import LocationManager
from weather_app.repository import LocationRepository, SettingsRepository

# Constants
VALID_TEMP_UNITS = ["F", "C"]
DEFAULT_TEMP_UNIT = "C"
DEFAULT_FORECAST_DAYS = 7


class Helpers:
    # Initialize shared resources as class variables
    weather_api = WeatherAPI()
    weather_display = WeatherDisplay()
    location_repo = LocationRepository()
    settings_repo = SettingsRepository()

    # Initialize components that require dependencies
    current_manager = CurrentWeatherManager(weather_api, weather_display)
    forecast_manager = ForecastManager(weather_api, weather_display)
    location_manager = LocationManager(weather_api, weather_display)
    app = WeatherApp()

    @classmethod
    def search_location_and_handle_results(cls, query: str, unit: str) -> Any:
        try:
            location_name = cls.normalize_location_input(query)
            print(f"Searching API for: {location_name}")
            results = cls.weather_api.search_city(location_name)
            print(f"API results: {results}")
            if not results or len(results) == 0:
                flash(f"No cities found matching '{query}'", "warning")
                return redirect(url_for("index"))

            # If only one result, go directly to weather
            if len(results) == 1:
                return redirect(
                    url_for(
                        "weather",
                        lat=results[0]["lat"],
                        lon=results[0]["lon"],
                        unit=unit,
                    )
                )

            # If multiple results, show them
            print(f"Searching API for: {location_name}")
            print(f"API results: {results}")
            return render_template(
                "search_results.html", results=results, query=query, unit=unit
            )
        except Exception as e:
            flash(f"Error finding location: {e}", "error")
            return redirect(url_for("index"))

    @staticmethod
    def get_normalized_unit(unit_param: Optional[str] = None) -> str:
        # Get unit from request or parameter

        unit = (unit_param or request.args.get("unit", DEFAULT_TEMP_UNIT)).upper()
        if unit not in VALID_TEMP_UNITS:
            unit = DEFAULT_TEMP_UNIT
        return unit

    @classmethod
    def get_location_by_coordinates(cls, lat: float, lon: float) -> Tuple[Any, str]:
        location = cls.location_repo.find_or_create_by_coordinates(
            name="Custom Location",  # Will be updated from API data
            latitude=lat,
            longitude=lon,
            country="",  # Will be updated from API data
            region=None,
        )
        coords = f"{lat},{lon}"
        return location, coords

    @classmethod
    def update_location_from_api_data(cls, location: Any, api_data: Dict) -> Any:
        if location.name == "Custom Location" and "location" in api_data:
            api_location = api_data["location"]
            location = cls.location_repo.update(
                location.id,
                {
                    "name": api_location["name"],
                    "country": api_location["country"],
                    "region": api_location.get("region"),
                },
            )
        return location

    @classmethod
    def save_weather_record(cls, location: Any, weather_data: Dict) -> None:
        try:
            cls.current_manager._save_weather_record(location, weather_data)
        except Exception as e:
            flash(f"Note: Failed to save weather data: {e}", "warning")

    @staticmethod
    def parse_coordinates_from_path(coordinates: str) -> Tuple[float, float]:
        parts = coordinates.split("/")
        if len(parts) != 2:
            raise ValueError("Invalid coordinates format")

        return float(parts[0]), float(parts[1])

    @staticmethod
    def normalize_location_input(location: str) -> str:
        """Normalize location input by handling common abbreviations"""
        mapping = {
            "UK": "United Kingdom",
            "U.S.": "United States",
            "USA": "United States",
            "UAE": "United Arab Emirates",
            # Add more as needed
        }
        for abbr, full in mapping.items():
            if location.strip().upper().endswith(abbr):
                return location.strip()[: -(len(abbr))].strip() + " " + full
        return location.strip()
