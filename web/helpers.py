import re
from datetime import datetime, timedelta
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

from .error_handlers import logger
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


def extract_location_with_geocoding(query_text: str) -> tuple[float, float]:
    """Extract location from query and return coordinates"""
    try:
        location_name = extract_location_from_query(query_text)
        return Helpers.geocode_with_disambiguation(location_name)
    except ValueError as e:
        raise ValueError(
            f"Could not extract or geocode location from query: {e}"
        ) from e


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
            # Add disambiguation here
            location_name = cls.disambiguate_location(location_name)

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
        # Validate coordinates first
        if not cls._validate_coordinates(lat, lon):
            raise ValueError(f"Invalid coordinates: {lat}, {lon}")

        # Try to find existing location first (within small radius)
        try:
            existing_location = cls.location_repo.find_by_coordinates_nearby(
                lat, lon, radius_km=1
            )
            if existing_location:
                coords = f"{lat},{lon}"
                return existing_location, coords
        except AttributeError:
            # Method doesn't exist, continue with regular approach
            pass
        except Exception as e:
            logger.warning(f"Error finding nearby location: {e}")

        # Get location data from geocoding API
        try:
            location_data = cls._reverse_geocode(lat, lon)

            location = cls.location_repo.find_or_create_by_coordinates(
                name=location_data.get("name", f"Location {lat:.2f},{lon:.2f}"),
                latitude=lat,
                longitude=lon,
                country=location_data.get("country", "Unknown"),
                region=location_data.get("region"),
            )

        except Exception as e:
            logger.warning(f"Error getting location data: {e}")
            # Fallback to basic location if API fails
            location = cls.location_repo.find_or_create_by_coordinates(
                name=f"Location {lat:.2f},{lon:.2f}",
                latitude=lat,
                longitude=lon,
                country="Unknown",
                region=None,
            )

        coords = f"{lat},{lon}"
        return location, coords

    @classmethod
    def _validate_coordinates(cls, lat: float, lon: float) -> bool:
        """Validate that coordinates are within valid ranges"""
        return -90 <= lat <= 90 and -180 <= lon <= 180

    @classmethod
    def _reverse_geocode(cls, lat: float, lon: float) -> dict:
        """Get location details from coordinates using weather API"""
        try:
            coords = (lat, lon)
            weather_data = cls.weather_api.get_weather(coords)

            if weather_data and "location" in weather_data:
                location_info = weather_data["location"]
                return {
                    "name": location_info.get("name", f"Location {lat:.2f},{lon:.2f}"),
                    "country": location_info.get("country", "Unknown"),
                    "region": location_info.get("region")
                    or (
                        location_info.get("tz_id", "").split("/")[-1]
                        if location_info.get("tz_id")
                        else None
                    ),
                }
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")

        # Fallback: return basic info
        return {
            "name": f"Location {lat:.2f},{lon:.2f}",
            "country": "Unknown",
            "region": None,
        }

    @classmethod
    def _reverse_geocode_alternative(cls, lat: float, lon: float) -> dict:
        """Alternative using a dedicated geocoding service"""
        import requests

        try:
            # Using OpenStreetMap Nominatim (free, no API key needed)
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {"lat": lat, "lon": lon, "format": "json", "accept-language": "en"}
            headers = {"User-Agent": "WeatherApp/1.0"}

            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()

            data = response.json()

            # Extract relevant information
            display_name = data.get("display_name", "")
            address = data.get("address", {})

            # Try to get city/town name
            name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("hamlet")
                or address.get("suburb")
                or display_name.split(",")[0]
                if display_name
                else f"Location {lat:.2f},{lon:.2f}"
            )

            country = address.get("country", "Unknown")
            region = (
                address.get("state") or address.get("province") or address.get("region")
            )

            return {"name": name, "country": country, "region": region}

        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return {
                "name": f"Location {lat:.2f},{lon:.2f}",
                "country": "Unknown",
                "region": None,
            }

    @staticmethod
    def disambiguate_location(location_name: str) -> str:
        """Disambiguate common ambiguous location names."""
        # Handle common ambiguous locations
        disambiguations = {
            "portland": "Portland, Oregon, USA",
            "cambridge": "Cambridge, Massachusetts, USA",
            "manchester": "Manchester, England, UK",
            "springfield": "Springfield, Illinois, USA",
            "richmond": "Richmond, Virginia, USA",
            "paris": "Paris, France",  # vs Paris, Texas
            "london": "London, England, UK",  # vs London, Ontario
            "birmingham": "Birmingham, Alabama, USA",  # vs Birmingham, UK
            "newcastle": "Newcastle, England, UK",  # vs Newcastle, Australia
            "york": "York, England, UK",  # vs York, Pennsylvania
            "athens": "Athens, Greece",  # vs Athens, Georgia
            "dublin": "Dublin, Ireland",  # vs Dublin, Ohio
            "florence": "Florence, Italy",  # vs Florence, South Carolina
            "milan": "Milan, Italy",  # vs Milan, Tennessee
            "rome": "Rome, Italy",  # vs Rome, Georgia
            "valencia": "Valencia, Spain",  # vs Valencia, California
            "moscow": "Moscow, Russia",  # vs Moscow, Idaho
            "alexandria": "Alexandria, Egypt",  # vs Alexandria, Virginia
            "columbus": "Columbus, Ohio, USA",  # Most populous Columbus
            "austin": "Austin, Texas, USA",  # Most well-known Austin
            "orlando": "Orlando, Florida, USA",  # Most well-known Orlando
        }

        normalized_name = location_name.lower().strip()

        if normalized_name in disambiguations:
            disambiguated = disambiguations[normalized_name]
            logger.info(f"Disambiguated '{location_name}' to '{disambiguated}'")
            return disambiguated

        return location_name

    @classmethod
    def geocode_with_disambiguation(cls, location_name: str) -> tuple[float, float]:
        """Geocode location with disambiguation for common ambiguous cities"""

        # First disambiguate the location
        disambiguated_name = cls.disambiguate_location(location_name)

        # Use your existing search API
        try:
            results = cls.weather_api.search_city(disambiguated_name)
            if results and len(results) > 0:
                # Return the first (most relevant) result
                return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as e:
            logger.error(f"Geocoding failed for '{disambiguated_name}': {e}")

        raise ValueError(f"Could not geocode location: {disambiguated_name}")

    @classmethod
    def validate_location_coordinates(
        cls, lat: float, lon: float, expected_location: str
    ) -> bool:
        """Validate that coordinates match the expected location."""
        try:
            location_data = cls._reverse_geocode(lat, lon)
            actual_name = location_data.get("name", "").lower()
            actual_country = location_data.get("country", "").lower()
            expected_lower = expected_location.lower()

            # Check if the location names match reasonably
            if "portland" in expected_lower:
                # For Portland, make sure we're not in Australia
                if "australia" in actual_country:
                    logger.warning(
                        f"Portland query resolved to Australia: {actual_name}, "
                        f"{actual_country}"
                    )
                    return False
                # Should be in USA (Oregon) or potentially Canada
                return "united states" in actual_country or "canada" in actual_country

            # Check for other specific problem cases
            problem_countries = {
                "cambridge": [
                    "united states",
                    "united kingdom",
                ],  # Allow both US and UK
                "manchester": [
                    "united kingdom",
                    "united states",
                ],  # Allow both UK and US
                "paris": ["france"],  # Should be France, not Texas
                "london": ["united kingdom"],  # Should be UK, not Ontario
                "dublin": ["ireland"],  # Should be Ireland, not Ohio
            }

            for city, allowed_countries in problem_countries.items():
                if city in expected_lower:
                    if not any(
                        country in actual_country for country in allowed_countries
                    ):
                        logger.warning(
                            f"{city} query resolved to wrong country: {actual_country}"
                        )
                        return False
                    break

            # General name matching for other locations
            return (
                expected_lower in actual_name
                or actual_name in expected_lower
                or any(
                    word in actual_name
                    for word in expected_lower.split()
                    if len(word) > 3
                )
            )

        except Exception as e:
            logger.error(f"Location validation failed: {e}")
            return True  # Don't block on validation errors

    @classmethod
    def update_location_from_api_data(cls, location: Any, api_data: dict) -> Any:
        if (
            hasattr(location, "name")
            and location.name == "Custom Location"
            and "location" in api_data
        ):
            api_location = api_data["location"]
            try:
                location = cls.location_repo.update(
                    location.id,
                    {
                        "name": api_location["name"],
                        "country": api_location["country"],
                        "region": api_location.get("region"),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to update location from API data: {e}")
        return location

    @classmethod
    def save_weather_record(cls, location: Any, weather_data: dict) -> None:
        try:
            cls.current_manager._save_weather_record(location, weather_data)
        except Exception as e:
            logger.warning(f"Failed to save weather data: {e}")
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

    @classmethod
    def get_date_range_for_query(cls, query_text: str) -> list[datetime.date]:
        """
        Parse natural language date queries and return a list of dates.

        Args:
            query_text: The natural language query text

        Returns:
            List of dates that match the query
        """
        query_lower = query_text.lower()
        today = datetime.now().date()
        target_dates = []

        # Tomorrow
        if "tomorrow" in query_lower:
            tomorrow = today + timedelta(days=1)
            target_dates = [tomorrow]

        # This weekend (upcoming Saturday and Sunday)
        elif "this weekend" in query_lower:
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.weekday() == 5:  # Today is Saturday
                saturday = today
            else:
                saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # Next weekend
        elif "next weekend" in query_lower:
            days_until_next_saturday = ((5 - today.weekday()) % 7) + 7
            saturday = today + timedelta(days=days_until_next_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # This week (Monday to Sunday of current week)
        elif "this week" in query_lower:
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            target_dates = [monday + timedelta(days=i) for i in range(7)]

        # Next week (Monday to Sunday of next week)
        elif "next week" in query_lower:
            days_since_monday = today.weekday()
            next_monday = today + timedelta(days=(7 - days_since_monday))
            target_dates = [next_monday + timedelta(days=i) for i in range(7)]

        # Specific weekdays
        elif any(day in query_lower for day in WEEKDAY_NAMES):
            for day_name, day_num in WEEKDAY_TO_NUMBER.items():
                if day_name in query_lower:
                    days_ahead = (day_num - today.weekday()) % 7
                    if days_ahead == 0:  # Today is the requested day
                        if "next" in query_lower:
                            days_ahead = 7  # Next occurrence
                    target_date = today + timedelta(days=days_ahead)
                    target_dates = [target_date]
                    break

        # General weekend (any weekend days in forecast)
        elif (
            "weekend" in query_lower
            and "this" not in query_lower
            and "next" not in query_lower
        ):
            # Find all weekend days in the forecast period
            for i in range(7):  # Check next 7 days
                check_date = today + timedelta(days=i)
                if check_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                    target_dates.append(check_date)

        # Today (default if no other matches)
        else:
            target_dates = [today]

        return target_dates

    @classmethod
    def filter_forecast_by_dates(
        cls, forecast_data: list[dict], target_dates: list[datetime.date]
    ) -> list[dict]:
        """
        Filter forecast data to only include specified dates.

        Args:
            forecast_data: List of forecast data dictionaries
            target_dates: List of dates to filter for

        Returns:
            Filtered list of forecast data
        """
        filtered_forecast = []
        try:
            for day in forecast_data:
                day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                if day_date in target_dates:
                    filtered_forecast.append(day)
        except (ValueError, KeyError) as e:
            logger.error(f"Error filtering forecast data: {e}")
            return forecast_data  # Return original data on error

        return filtered_forecast if filtered_forecast else forecast_data
