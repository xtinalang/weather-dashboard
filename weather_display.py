import logging
from typing import Optional, Dict, Any, List
from emoji import get_weather_emoji

logger = logging.getLogger("weather_app")

class WeatherDisplay:
    @staticmethod
    def show_city(city: Optional[List[Dict[str, Any]]]) -> None:
        if not city:
            print("No city found.")
            return
        print("\n📍 Found city:")
        for i, location in enumerate(city, 1):
            print(f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}")
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")

    @staticmethod
    def show_current_weather(weather_data: Optional[Dict[str, Any]]) -> None:
        if not weather_data:
            print("❌ Could not retrieve weather data.")
            return
        location = weather_data["location"]
        current = weather_data["current"]
        emoji = get_weather_emoji(current["condition"]["text"])
        print(f"\n{emoji} Weather in {location['name']}, {location['country']}: {current['condition']['text']}")
        print(f"Temperature: {current['temp_c']}°C / {current['temp_f']}°F")

    @staticmethod
    def show_forecast(weather_data: Optional[Dict[str, Any]]) -> None:
        forecast = weather_data.get("forecast", {}).get("forecastday", [])
        print("\n7-Day Forecast:")
        for day in forecast:
            date = day["date"]
            emoji = get_weather_emoji(day["day"]["condition"]["text"])
            print(f"{date} - {emoji} {day['day']['condition']['text']}")
