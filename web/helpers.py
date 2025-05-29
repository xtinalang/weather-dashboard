import re
from typing import Any, Optional

from flask import flash, redirect, render_template, request, url_for

from weather_app.api import WeatherAPI
from weather_app.cli_app import WeatherApp
from weather_app.current import CurrentWeatherManager
from weather_app.display import WeatherDisplay
from weather_app.forecast import ForecastManager
from weather_app.location import LocationManager
from weather_app.repository import LocationRepository, SettingsRepository
from weather_app.weather_types import LocationData, TemperatureUnit, WeatherData

from .utils import CELSIUS, DEFAULT_TEMP_UNIT, VALID_TEMP_UNITS

# Location abbreviation mapping constant
LOCATION_ABBREVIATION_MAPPING = {
    "UK": "United Kingdom",
    "U.S.": "United States",
    "USA": "United States",
    "UAE": "United Arab Emirates",
    # Add more as needed
}

# Weekday constants for natural language date parsing
WEEKDAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

WEEKDAY_TO_NUMBER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def extract_location_from_query(query_text: str) -> str:
    """Extract location from natural language query using multiple patterns."""

    # Helper function to check if text looks like a question
    def is_question_phrase(text):
        question_patterns = [
            r"^what\b.*",
            r"^how\b.*",
            r"^when\b.*",
            r"^where\b.*",
            r"^why\b.*",
            r"^which\b.*",
            r"^is\b.*",
            r"^are\b.*",
            r"^do\b.*",
            r"^does\b.*",
            r"^will\b.*",
            r"^can\b.*",
            r"^should\b.*",
            r"^would\b.*",
            r"^could\b.*",
            r".*\blike\s*\?.*",
        ]
        return any(
            re.match(pattern, text.strip(), re.IGNORECASE)
            for pattern in question_patterns
        )

    patterns = [
        # Pattern 1: Traditional "in/for Location" format
        (
            (
                r"\b(?:in|for)\s+([A-Za-z\s,.''-]+?)"
                r"(?:\s+(?:on|at|for|,|tomorrow|today|this|next)|[?!](?:\s|$)|$)"
            ),
            lambda m: m.group(1).strip(),
        ),
        # Pattern 2: Location followed by weather keywords (with filtering)
        (
            r"^([A-Za-z\s,.''-]+?)\s+(?:weather|forecast|temperature|temp)",
            lambda m: (
                m.group(1).strip()
                if not is_question_phrase(query_text) and len(m.group(1).split()) <= 3
                else None
            ),
        ),
        # Pattern 3: Weather keywords followed by location (with question filtering)
        (
            (
                r"(?:weather|forecast|temperature|temp)\s+(?:in|for|at)?\s*"
                r"([A-Za-z\s,.''-]+?)"
                r"(?:\s+(?:tomorrow|today|this|next|on)|[?!](?:\s|$)|$)"
            ),
            lambda m: (
                m.group(1).strip() if not is_question_phrase(query_text) else None
            ),
        ),
        # Pattern 4: Simple location at the beginning (fixed to capture correctly)
        (
            (
                r"^([A-Za-z\s,.''-]+?)"
                r"(?:\s+(?:weather|forecast|temperature|temp|tomorrow|today|this|next)"
                r"\b)"
            ),
            lambda m: (
                m.group(1).strip()
                if len(m.group(1).split()) >= 1 and not is_question_phrase(query_text)
                else None
            ),
        ),
    ]

    for pattern, extractor in patterns:
        try:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if not match:
                raise ValueError("Pattern did not match")

            location = extractor(match)
            if not location:
                raise ValueError("Extractor returned None")

            return location.strip()

        except (ValueError, AttributeError):
            continue

    raise ValueError("No location pattern matched")


def get_weather_data(
    coords: tuple[float, float], unit: TemperatureUnit, weather_api: WeatherAPI
) -> tuple[WeatherData, LocationData]:
    """Get weather data for given coordinates."""
    weather_data = weather_api.get_weather(coords)
    if not weather_data:
        raise ValueError("Failed to get weather data")

    location_obj, _ = Helpers.get_location_by_coordinates(coords[0], coords[1])
    location_obj = Helpers.update_location_from_api_data(location_obj, weather_data)

    # Format the weather data
    formatted_data = {
        "current": {
            "temp_c": weather_data["current"]["temp_c"],
            "temp_f": weather_data["current"]["temp_f"],
            "feelslike_c": weather_data["current"]["feelslike_c"],
            "feelslike_f": weather_data["current"]["feelslike_f"],
            "humidity": weather_data["current"]["humidity"],
            "condition": weather_data["current"]["condition"],
            "wind_kph": weather_data["current"]["wind_kph"],
            "wind_mph": weather_data["current"]["wind_mph"],
            "wind_dir": weather_data["current"]["wind_dir"],
            "pressure_mb": weather_data["current"]["pressure_mb"],
            "precip_mm": weather_data["current"]["precip_mm"],
            "uv": weather_data["current"]["uv"],
            "last_updated": weather_data["current"]["last_updated"],
        }
    }

    return formatted_data, location_obj


def get_forecast_data(
    coords: tuple[float, float], unit: TemperatureUnit, weather_api: WeatherAPI
) -> list[dict[str, Any]]:
    """Get forecast data for given coordinates."""
    forecast_data = weather_api.get_forecast(coords)
    if not forecast_data:
        raise ValueError("Failed to get forecast data")

    # Format the forecast data
    formatted_forecast = []
    for day in forecast_data["forecast"]["forecastday"]:
        formatted_day = {
            "date": day["date"],
            "max_temp": (
                day["day"]["maxtemp_c"] if unit == CELSIUS else day["day"]["maxtemp_f"]
            ),
            "min_temp": (
                day["day"]["mintemp_c"] if unit == CELSIUS else day["day"]["mintemp_f"]
            ),
            "condition": day["day"]["condition"]["text"],
            "icon": day["day"]["condition"]["icon"],
            "chance_of_rain": day["day"]["daily_chance_of_rain"],
            "chance_of_snow": day["day"]["daily_chance_of_snow"],
            "maxwind_kph": day["day"]["maxwind_kph"],
            "maxwind_mph": day["day"]["maxwind_mph"],
            "wind_speed": day["day"]["maxwind_kph"]
            if unit == CELSIUS
            else day["day"]["maxwind_mph"],
            "wind_unit": "km/h" if unit == CELSIUS else "mph",
            "humidity": day["day"]["avghumidity"],
            "totalprecip_mm": day["day"]["totalprecip_mm"],
            "totalprecip_in": day["day"]["totalprecip_in"],
            "avghumidity": day["day"]["avghumidity"],
            "uv": day["day"]["uv"],
        }
        formatted_forecast.append(formatted_day)

    return formatted_forecast


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
    def get_location_by_coordinates(cls, lat: float, lon: float) -> tuple[Any, str]:
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
    def update_location_from_api_data(cls, location: Any, api_data: dict) -> Any:
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
    def save_weather_record(cls, location: Any, weather_data: dict) -> None:
        try:
            cls.current_manager._save_weather_record(location, weather_data)
        except Exception as e:
            flash(f"Note: Failed to save weather data: {e}", "warning")

    @staticmethod
    def parse_coordinates_from_path(coordinates: str) -> tuple[float, float]:
        parts = coordinates.split("/")
        if len(parts) != 2:
            raise ValueError("Invalid coordinates format")

        return float(parts[0]), float(parts[1])

    @staticmethod
    def normalize_location_input(location: str) -> str:
        """Normalize location input by handling common abbreviations"""
        for abbr, full in LOCATION_ABBREVIATION_MAPPING.items():
            if location.strip().upper().endswith(abbr):
                return location.strip()[: -(len(abbr))].strip() + " " + full
        return location.strip()
