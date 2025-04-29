from weather_api import WeatherAPI
from weather_display import WeatherDisplay
from location_manager import LocationManager
import logging

logger = logging.getLogger("weather_app")

class WeatherApp:
    def __init__(self):
        self.weather_api = WeatherAPI()
        self.display = WeatherDisplay()
        self.location_manager = LocationManager(self.weather_api, self.display)

    def run(self):
        print("Welcome to the Weather App!")
        print("==========================")

        try:
            location = self.location_manager.get_location()
            if not location:
                print("No location selected. Exiting.")
                return

            weather_data = self.weather_api.get_weather(location)
            if weather_data:
                self.display.show_current_weather(weather_data)
                self.display.show_forecast(weather_data)
            else:
                print("Could not retrieve weather data.")
        except KeyboardInterrupt:
            print("\nApplication terminated by user.")
