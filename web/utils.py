from typing import Any, Literal

CELSIUS = "C"
FAHRENHEIT = "F"
VALID_UNITS = {CELSIUS, FAHRENHEIT}
TemperatureUnit = Literal[CELSIUS, FAHRENHEIT]
VALID_TEMP_UNITS = ["F", "C"]
DEFAULT_TEMP_UNIT = "C"
DEFAULT_FORECAST_DAYS = 7

# Form choices constants
TEMPERATURE_UNIT_CHOICES = [(CELSIUS, "Celsius (°C)"), (FAHRENHEIT, "Fahrenheit (°F)")]

FORECAST_DAYS_CHOICES = [
    ("1", "1 Day"),
    ("3", "3 Days"),
    ("5", "5 Days"),
    ("7", "7 Days"),
]

DEFAULT_FORECAST_DAYS_STR = "7"


class Utility:
    @staticmethod
    def format_weather_data(
        weather_data: dict[str, Any], unit: str = "C"
    ) -> dict[str, Any]:
        if not weather_data:
            return {}

        result = {
            "location": {
                "name": weather_data["location"]["name"],
                "region": weather_data["location"]["region"],
                "country": weather_data["location"]["country"],
            },
            "current": {
                "condition": weather_data["current"]["condition"]["text"],
                "icon": weather_data["current"]["condition"]["icon"],
                "humidity": weather_data["current"]["humidity"],
                "wind_kph": weather_data["current"]["wind_kph"],
                "wind_mph": weather_data["current"]["wind_mph"],
                "wind_dir": weather_data["current"]["wind_dir"],
                "pressure_mb": weather_data["current"]["pressure_mb"],
                "pressure_in": weather_data["current"]["pressure_in"],
                "precip_mm": weather_data["current"]["precip_mm"],
                "precip_in": weather_data["current"]["precip_in"],
                "last_updated": weather_data["current"][
                    "last_updated"
                ],  # still need to add more to this.
            },
            "unit": unit,
        }

        # Add temperature based on unit
        if unit == "F":
            result["current"]["temp"] = weather_data["current"]["temp_f"]
            result["current"]["feelslike"] = weather_data["current"]["feelslike_f"]
        else:
            result["current"]["temp"] = weather_data["current"]["temp_c"]
            result["current"]["feelslike"] = weather_data["current"]["feelslike_c"]

        # Add forecast if available
        if "forecast" in weather_data:
            result["forecast"] = []
            for day in weather_data["forecast"].get("forecastday", []):
                forecast_day = {
                    "date": day["date"],
                    "condition": day["day"]["condition"]["text"],
                    "icon": day["day"]["condition"]["icon"],
                    "humidity": day["day"].get("avghumidity", "N/A"),
                    "chance_of_rain": day["day"].get("daily_chance_of_rain", "N/A"),
                    "chance_of_snow": day["day"].get("daily_chance_of_snow", "N/A"),
                }

                # Add temperature based on unit
                if unit == "C":
                    forecast_day["max_temp"] = day["day"]["maxtemp_c"]
                    forecast_day["min_temp"] = day["day"]["mintemp_c"]
                else:
                    forecast_day["max_temp"] = day["day"]["maxtemp_f"]
                    forecast_day["min_temp"] = day["day"]["mintemp_f"]

                # Add sunrise/sunset if available
                if "astro" in day:
                    forecast_day["sunrise"] = day["astro"].get("sunrise", "N/A")
                    forecast_day["sunset"] = day["astro"].get("sunset", "N/A")

                result["forecast"].append(forecast_day)

        return result
