import requests
import logging
from decouple import config
from typing import Optional, Dict, Any, List

logger = logging.getLogger("weather_app")

class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or config("WEATHER_API_KEY")
        self.base_url = "http://api.weatherapi.com/v1/"

    def get_weather(self, location: str) -> Optional[Dict[str, Any]]:
        try:
            params = {"q": location, "key": self.api_key, "days": 7, "aqi": "yes"}
            response = requests.get(f"{self.base_url}/forecast.json", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Weather fetch error: {e}", exc_info=True)
            print("Error getting weather data.")
            return None

    def search_city(self, query: str) -> Optional[List[Dict[str, Any]]]:
        try:
            params = {"q": query, "key": self.api_key}
            response = requests.get(f"{self.base_url}/search.json", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"City search error: {e}", exc_info=True)
            print("Error searching for city.")
            return None
