import logging
from typing import Any, Dict, List, Optional

from emoji import get_weather_emoji

logger = logging.getLogger("weather_app")


class WeatherDisplay:
    """Handles all output and presentation of weather information."""

    def __init__(self) -> None:
        logger.debug("Initializing WeatherDisplay")

    @staticmethod
    def show_city(city: Optional[List[Dict[str, Any]]]) -> None:
        """Display list of matching cities for user to choose from."""
        logger.info("Displaying city information")
        if not city:
            logger.warning("No city data to display")
            print("No city found.")
            return

        print("\n📍 Found cities:")
        print("=" * 50)

        for i, location in enumerate(city, 1):
            logger.debug(f"City {i}: {location['name']}")
            print(
                f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}"
            )
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            print(f"   URL: {location.get('url', 'N/A')}")
            print("-" * 50)

    @staticmethod
    def show_current_weather(
        weather_data: Optional[Dict[str, Any]], unit: str = "C"
    ) -> None:
        """Display current weather for a location."""
        logger.info("Displaying current weather")
        if not weather_data:
            logger.warning("No weather data to display")
            print("❌ Could not retrieve weather data.")
            return

        location = weather_data["location"]
        current = weather_data["current"]
        condition_text = current["condition"]["text"]
        emoji = get_weather_emoji(condition_text)

        print(
            f"\nWeather in 📍 {location['name']}, {location['region']}, {location['country']}:"
        )
        print(f"{emoji} {condition_text}")
        # Disply temperature in C or F
        # if unit == "F":
        #     print(f"🌡️ Temperature: {current['temp_f']}°F")
        #     print(f"🌡️ Feels like: {current['feelslike_f']}°F")
        # else:
        #     print(f"🌡️ Temperature: {current['temp_c']}°C")
        #     print(f"🌡️ Feels like: {current['feelslike_c']}°C")

        print(f"🌡️ Temperature: {current['temp_c']}°C / {current['temp_f']}°F")
        print(f"🌡️ Feels like: {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        print(f"💧 Humidity: {current['humidity']}%")
        print(
            f"💨 Wind: {current['wind_kph']} kph / {current['wind_mph']} mph, {current['wind_dir']}"
        )
        print(f"🌫️ Visibility: {current['vis_km']} km / {current['vis_miles']} miles")
        print(f"📊 Pressure: {current['pressure_mb']} mb / {current['pressure_in']} in")
        print(
            f"☔ Precipitation: {current['precip_mm']} mm / {current['precip_in']} in"
        )
        print(f"🔄 Last updated: {current['last_updated']}")

    @staticmethod
    def show_forecast(weather_data: Optional[Dict[str, Any]], unit: str = "C") -> None:
        """Display 7-day weather forecast."""
        logger.info("Displaying weather forecast")
        if not weather_data or "forecast" not in weather_data:
            logger.warning("No forecast data to display")
            return

        forecast = weather_data["forecast"]["forecastday"]

        print("\n🗓️ 7-Day Weather Forecast:")
        print("=" * 40)

        for day in forecast:
            date = day["date"]
            day_data = day["day"]
            astro = day["astro"]
            condition_text = day_data["condition"]["text"]
            emoji = get_weather_emoji(condition_text)

            print(f"\n📅 Date: {date}")
            print(f"{emoji} {condition_text}")
            # Display min/max C or F in forcast
            # if unit == "F":
            #     print(f"🌡️ Max: {day_data['maxtemp_f']}°F")
            #     print(f"🌡️ Min: {day_data['mintemp_f']}°F")
            # else:
            #     print(f"🌡️ Max: {day_data['maxtemp_c']}°C")
            #     print(f"🌡️ Min: {day_data['mintemp_c']}°C")

            print(f"🌡️ Max: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
            print(f"🌡️ Min: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
            print(f"☔ Chance of rain: {day_data['daily_chance_of_rain']}%")
            print(f"❄️ Chance of snow: {day_data['daily_chance_of_snow']}%")
            print(f"🌄 Sunrise: {astro['sunrise']} | 🌇 Sunset: {astro['sunset']}")
            print("-" * 40)
