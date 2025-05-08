import logging
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypedDict,
    Union,
    cast,
)

import requests
from decouple import config

logger = logging.getLogger("weather_app")


# Define typed dictionaries for API responses
class WeatherCondition(TypedDict, total=False):
    text: str
    icon: str
    code: int


class CurrentWeather(TypedDict, total=False):
    last_updated: str
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    condition: WeatherCondition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    is_day: int
    uv: float
    gust_mph: float
    gust_kph: float


class LocationInfo(TypedDict, total=False):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


class DayForecast(TypedDict, total=False):
    maxtemp_c: float
    maxtemp_f: float
    mintemp_c: float
    mintemp_f: float
    avgtemp_c: float
    avgtemp_f: float
    maxwind_mph: float
    maxwind_kph: float
    totalprecip_mm: float
    totalprecip_in: float
    totalsnow_cm: float
    avgvis_km: float
    avgvis_miles: float
    avghumidity: int
    daily_will_it_rain: int
    daily_chance_of_rain: int
    daily_will_it_snow: int
    daily_chance_of_snow: int
    condition: WeatherCondition
    uv: float


class AstroInfo(TypedDict, total=False):
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: str
    is_moon_up: int
    is_sun_up: int


class ForecastDay(TypedDict, total=False):
    date: str
    date_epoch: int
    day: DayForecast
    astro: AstroInfo
    hour: List[Dict[str, Any]]


class ForecastData(TypedDict, total=False):
    forecastday: List[ForecastDay]


class WeatherResponse(TypedDict, total=False):
    location: LocationInfo
    current: CurrentWeather
    forecast: ForecastData


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
        """
        Initialize the Weather API with an API key.

        Args:
            api_key: API key for authentication, if None, read from environment

        Raises:
            ValueError: If API key is not found
        """
        try:
            self.api_key: str = api_key or config("WEATHER_API_KEY")
            if not self.api_key:
                err_msg = (
                    "Weather API key not found. Please set WEATHER_API_KEY in .env file"
                )
                raise ValueError(err_msg)
        except Exception as e:
            logger.error(f"Failed to initialize WeatherAPI: {e}")
            raise ValueError("Failed to initialize WeatherAPI") from e
        self.base_url: str = "https://api.weatherapi.com/v1/"

    def get_weather(
        self, location: str, date: Optional[str] = None
    ) -> Optional[WeatherResponse]:
        """
        Get current weather and forecast for a location.

        Args:
            location: Location string (can be coordinates like "lat,lon")
            date: Optional date string for historical weather (YYYY-MM-DD)

        Returns:
            Weather data response or None if request failed
        """
        try:
            endpoint: str = "forecast.json"
            params: Dict[str, Union[str, int]] = {
                "q": location,
                "key": self.api_key,
                "days": 7,
                "aqi": "yes",
            }

            # Add date for historical weather
            if date:
                endpoint = "history.json"
                params["dt"] = date

            request_url: str = f"{self.base_url}{endpoint}"
            response: requests.Response = requests.get(request_url, params=params)
            response.raise_for_status()

            return cast(WeatherResponse, response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather fetch error: {e}", exc_info=True)
            print(f"Error getting weather data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An unexpected error occurred while fetching weather data.")
            return None

    def get_forecast(self, location: str, days: int = 7) -> Optional[WeatherResponse]:
        """
        Get weather forecast for a location.

        Args:
            location: Location string (can be coordinates like "lat,lon")
            days: Number of days to forecast (1-7)

        Returns:
            Dictionary with forecast data or None if request failed
        """
        try:
            # Ensure days is within valid range
            valid_days: int = max(1, min(days, 7))

            params: Dict[str, Union[str, int]] = {
                "q": location,
                "key": self.api_key,
                "days": valid_days,
                "aqi": "no",
            }

            request_url: str = f"{self.base_url}forecast.json"
            response: requests.Response = requests.get(request_url, params=params)
            response.raise_for_status()

            return cast(WeatherResponse, response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast fetch error: {e}", exc_info=True)
            print(f"Error getting forecast data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in forecast: {e}", exc_info=True)
            print("An unexpected error occurred while fetching forecast data.")
            return None

    def search_city(self, query: str) -> Optional[List[CitySearchResult]]:
        """
        Search for a city by name.

        Args:
            query: City name or partial name to search for

        Returns:
            List of matching cities or None if request failed
        """
        try:
            params: Dict[str, str] = {"q": query, "key": self.api_key}
            request_url: str = f"{self.base_url}search.json"

            response: requests.Response = requests.get(request_url, params=params)
            response.raise_for_status()

            return cast(List[CitySearchResult], response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"City search error: {e}", exc_info=True)
            print(f"Error searching for city: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An unexpected error occurred while searching for city.")
            return None
