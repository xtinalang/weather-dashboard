import logging
from typing import (
    Optional,
    TypedDict,
    Union,
    cast,
)

import requests
from decouple import config

from .weather_types import WeatherResponse

logger = logging.getLogger("weather_app")

WEATHER_URL: str = "https://api.weatherapi.com/v1/"

# Request timeout configuration (in seconds)
CONNECTION_TIMEOUT: int = 5  # Maximum time to wait for connection establishment
READ_TIMEOUT: int = 15  # Maximum time to wait for server response
REQUEST_TIMEOUT: tuple[int, int] = (CONNECTION_TIMEOUT, READ_TIMEOUT)

# Define typed dictionaries for API responses


class CitySearchResult(TypedDict, total=False):
    id: int
    name: str
    region: str
    country: str
    lat: float
    lon: float
    url: str


class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None) -> None:
        try:
            self.api_key: str = api_key or config("WEATHER_API_KEY")
            if not self.api_key:
                err_msg: str = (
                    "Weather API key not found. Please set WEATHER_API_KEY in .env file"
                )
                raise ValueError(err_msg)
        except Exception as e:
            logger.error(f"Failed to initialize WeatherAPI: {e}")
            raise ValueError("Failed to initialize WeatherAPI") from e

    def get_weather(
        self, location: str, date: Optional[str] = None
    ) -> Optional[WeatherResponse]:
        try:
            endpoint: str = "forecast.json"
            params: dict[str, Union[str, int]] = {
                "q": location,
                "key": self.api_key,
                "days": 7,
                "aqi": "yes",
            }

            # Add date for historical weather
            if date:
                endpoint = "history.json"
                params["dt"] = date

            request_url: str = f"{WEATHER_URL}{endpoint}"
            response: requests.Response = requests.get(
                request_url, params=params, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            return cast(WeatherResponse, response.json())
        except requests.exceptions.Timeout:
            logger.error("Weather API request timed out")
            print("Weather service is taking too long to respond. Please try again.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather fetch error: {e}", exc_info=True)
            print(f"Error getting weather data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An unexpected error occurred while fetching weather data.")
            return None

    def get_forecast(self, location: str, days: int = 7) -> Optional[WeatherResponse]:
        try:
            # Ensure days is within valid range
            valid_days: int = max(1, min(days, 7))

            params: dict[str, Union[str, int]] = {
                "q": location,
                "key": self.api_key,
                "days": valid_days,
                "aqi": "no",
            }

            request_url: str = f"{WEATHER_URL}forecast.json"
            response: requests.Response = requests.get(
                request_url, params=params, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            return cast(WeatherResponse, response.json())
        except requests.exceptions.Timeout:
            logger.error("Forecast API request timed out")
            print("Forecast service is taking too long to respond. Please try again.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast fetch error: {e}", exc_info=True)
            print(f"Error getting forecast data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in forecast: {e}", exc_info=True)
            print("An unexpected error occurred while fetching forecast data.")
            return None

    def search_city(self, query: str) -> Optional[list[CitySearchResult]]:
        try:
            params: dict[str, str] = {"q": query, "key": self.api_key}
            request_url: str = f"{WEATHER_URL}search.json"

            response: requests.Response = requests.get(
                request_url, params=params, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            return cast(list[CitySearchResult], response.json())
        except requests.exceptions.Timeout:
            logger.error("City search API request timed out")
            print("City search is taking too long to respond. Please try again.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"City search error: {e}", exc_info=True)
            print(f"Error searching for city: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An unexpected error occurred while searching for city.")
            return None
