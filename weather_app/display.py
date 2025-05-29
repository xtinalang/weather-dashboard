import logging
from typing import Any, Optional

from .emoji import get_weather_emoji

logger = logging.getLogger("weather_app")


class WeatherDisplay:
    logger.debug("Initializing WeatherDisplay")

    @staticmethod
    def show_error(message: str) -> None:
        """Display an error message to the user."""
        logger.error(message)
        print(f"❌ {message}")

    @staticmethod
    def show_message(message: str) -> None:
        """Display an informational message to the user."""
        logger.info(message)
        print(f"ℹ️ {message}")

    @staticmethod
    def show_warning(message: str) -> None:
        """Display a warning message to the user."""
        logger.warning(message)
        print(f"⚠️ {message}")

    @staticmethod
    def show_city(city: Optional[list[dict[str, Any]]]) -> None:
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
                f"{i}. {location['name']}, {location.get('region', 'N/A')}, "
                f"{location['country']}"
            )
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            print(f"   URL: {location.get('url', 'N/A')}")
            print("-" * 50)

    @staticmethod
    def show_current_weather(
        weather_data: Optional[dict[str, Any]], unit: str = "C"
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
            f"\nWeather in 📍 {location['name']}, {location['region']}, "
            f"{location['country']}:"
        )
        print(f"{emoji} {condition_text}")

        # Display temperature based on unit preference
        if unit == "F":
            print(f"🌡️ Temperature: {current['temp_f']}°F")
            print(f"🌡️ Feels like: {current['feelslike_f']}°F")
        else:
            print(f"🌡️ Temperature: {current['temp_c']}°C")
            print(f"🌡️ Feels like: {current['feelslike_c']}°C")

        print(f"💧 Humidity: {current['humidity']}%")
        print(
            f"💨 Wind: {current['wind_kph']} kph / {current['wind_mph']} mph, "
            f"{current['wind_dir']}"
        )
        print(f"🌫️ Visibility: {current['vis_km']} km / {current['vis_miles']} miles")
        print(f"📊 Pressure: {current['pressure_mb']} mb / {current['pressure_in']} in")
        print(
            f"☔ Precipitation: {current['precip_mm']} mm / {current['precip_in']} in"
        )
        print(f"🔄 Last updated: {current['last_updated']}")

    @staticmethod
    def show_forecast(
        weather_data: Optional[dict[str, Any]], unit: str = "C", days: int = None
    ) -> None:
        logger.info("Displaying weather forecast")
        if not weather_data:
            logger.warning("No weather data to display")
            print("❌ Could not retrieve forecast data.")
            return

        # Check if forecast data exists
        if "forecast" not in weather_data:
            logger.warning("No forecast data in weather response")
            print("❌ No forecast data available.")
            return

        # Get forecast days
        forecast = weather_data["forecast"].get("forecastday", [])
        if not forecast:
            logger.warning("Empty forecast data")
            print("❌ No forecast days available.")
            return

        # Limit to the specified number of days if requested
        forecast_days = forecast
        if days is not None:
            forecast_days = forecast[: min(days, len(forecast))]

        # Display the forecast header with actual number of days
        num_days = len(forecast_days)
        print(f"\n🗓️ {num_days}-Day Weather Forecast:")
        print("=" * 40)

        for day in forecast_days:
            # Skip if day data structure is invalid
            if not isinstance(day, dict) or "date" not in day or "day" not in day:
                logger.warning(f"Invalid day data format: {day}")
                continue

            try:
                date = day["date"]
                day_data = day["day"]
                astro = day.get("astro", {})

                condition_text = day_data.get("condition", {}).get("text", "Unknown")
                emoji = get_weather_emoji(condition_text)

                print(f"\n📅 Date: {date}")
                print(f"{emoji} {condition_text}")

                # Display temperature based on unit preference
                if unit.upper() == "F":
                    print(f"🌡️ Max: {day_data.get('maxtemp_f', 'N/A')}°F")
                    print(f"🌡️ Min: {day_data.get('mintemp_f', 'N/A')}°F")
                else:
                    print(f"🌡️ Max: {day_data.get('maxtemp_c', 'N/A')}°C")
                    print(f"🌡️ Min: {day_data.get('mintemp_c', 'N/A')}°C")

                # Handle optional forecast fields
                chance_of_rain = day_data.get("daily_chance_of_rain", "N/A")
                chance_of_snow = day_data.get("daily_chance_of_snow", "N/A")
                sunrise = astro.get("sunrise", "N/A")
                sunset = astro.get("sunset", "N/A")

                print(f"☔ Chance of rain: {chance_of_rain}%")
                print(f"❄️ Chance of snow: {chance_of_snow}%")
                print(f"🌄 Sunrise: {sunrise} | 🌇 Sunset: {sunset}")
                print("-" * 40)
            except Exception as e:
                logger.error(f"Error displaying forecast day: {e}")
                print(
                    f"❌ Error displaying forecast for "
                    f"{day.get('date', 'unknown date')}"
                )

    @staticmethod
    def show_historical_weather(
        weather_data: Optional[dict[str, Any]], date_str: str
    ) -> None:
        logger.info(f"Displaying historical weather for {date_str}")
        if not weather_data:
            logger.warning("No historical weather data to display")
            print("❌ Could not retrieve historical weather data.")
            return

        # Check if historical forecast data exists
        if "forecast" not in weather_data:
            logger.warning("No historical data in weather response")
            print("❌ No historical data available.")
            return

        # Get forecast day matching the date
        forecast = weather_data["forecast"].get("forecastday", [])
        historical_day = None

        for day in forecast:
            if day.get("date") == date_str:
                historical_day = day
                break

        if not historical_day:
            logger.warning(f"No historical data found for {date_str}")
            print(f"❌ No historical data available for {date_str}.")
            return

        try:
            day_data = historical_day["day"]
            location = weather_data["location"]

            print(f"\n📅 Historical Weather for {date_str}")
            print(
                f"📍 {location['name']}, {location.get('region', '')}, "
                f"{location['country']}"
            )
            print("=" * 40)

            condition_text = day_data.get("condition", {}).get("text", "Unknown")
            emoji = get_weather_emoji(condition_text)

            print(f"{emoji} {condition_text}")
            print(
                f"🌡️ Average: {day_data.get('avgtemp_c', 'N/A')}°C / "
                f"{day_data.get('avgtemp_f', 'N/A')}°F"
            )
            print(
                f"🌡️ Max: {day_data.get('maxtemp_c', 'N/A')}°C / "
                f"{day_data.get('maxtemp_f', 'N/A')}°F"
            )
            print(
                f"🌡️ Min: {day_data.get('mintemp_c', 'N/A')}°C / "
                f"{day_data.get('mintemp_f', 'N/A')}°F"
            )
            print(f"💧 Average Humidity: {day_data.get('avghumidity', 'N/A')}%")
            print(f"☔ Total Precipitation: {day_data.get('totalprecip_mm', 'N/A')} mm")
            print(f"🌬️ Max Wind: {day_data.get('maxwind_kph', 'N/A')} kph")

            # Additional info if available
            if "uv" in day_data:
                print(f"☀️ UV Index: {day_data['uv']}")

        except Exception as e:
            logger.error(f"Error displaying historical weather: {e}")
            print(f"❌ Error displaying historical weather for {date_str}")
