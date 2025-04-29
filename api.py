import requests
import logging
from decouple import config
from typing import Optional, Dict, Any, List

logger = logging.getLogger("weather_app")

class WeatherAPI:
    """Handles communication with the WeatherAPI.com service."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        logger.debug("Initializing WeatherAPI")
        self.api_key: str = api_key or config("WEATHER_API_KEY")
        self.base_url: str = "http://api.weatherapi.com/v1/"
        logger.debug(f"Base URL set to: {self.base_url}")

    def get_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch 7-day forecast and current weather data for a given location."""
        logger.info(f"Fetching weather for: {location}")
        try:
            params: Dict[str, Any] = {
                "q": location,
                "key": self.api_key,
                "days": 7,
                "aqi": "yes"
            }
            response = requests.get(f"{self.base_url}forecast.json", params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"API error: {data['error']['message']}")
                print(f"API error: {data['error']['message']}")
                return None

            logger.debug("Weather data successfully retrieved")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching weather: {e}", exc_info=True)
            print("A network error occurred while fetching weather data.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An unexpected error occurred while getting weather.")
            return None

    def search_city(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search for a city name using WeatherAPI's autocomplete/search endpoint."""
        logger.info(f"Searching for city: {query}")
        try:
            params = {"q": query, "key": self.api_key}
            response = requests.get(f"{self.base_url}search.json", params=params)
            response.raise_for_status()
            location_data = response.json()

            if isinstance(location_data, dict) and "error" in location_data:
                logger.error(f"API error: {location_data['error']['message']}")
                print(f"API error: {location_data['error']['message']}")
                return None

            logger.debug(f"Found {len(location_data)} location(s)")
            return location_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while searching city: {e}", exc_info=True)
            print("A network error occurred while searching for city.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during city search: {e}", exc_info=True)
            print("An unexpected error occurred while searching for city.")
            return None
