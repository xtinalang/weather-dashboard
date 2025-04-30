# Main WeatherApp (application orchestration)
from api import WeatherAPI
from display import WeatherDisplay
from location import LocationManager
import logging

logger = logging.getLogger("weather_app")

class WeatherApp:
    def __init__(self):
        logger.info("Initializing WeatherApp components")
        self.weather_api = WeatherAPI()
        self.display = WeatherDisplay()
        self.location_manager = LocationManager(self.weather_api, self.display)
        # self.unit = "C"  # Default to Celsius

    def run(self):
        """Main application flow"""
        print("Welcome to the Weather App!")
        print("==========================")

        # unit_choice = self.user_input.get_temperature_unit()
        # if unit_choice == "2":
        #     self.unit = "F"
        # else:
        #     self.unit = "C"

        try:
            location = self.location_manager.get_location()
            if not location:
                logger.warning("No location selected")
                print("No location selected. Exiting application.")
                return

            logger.info(f"Fetching weather for location: {location}")
            weather_data = self.weather_api.get_weather(location)

            if weather_data:
                logger.info("Weather data retrieved successfully")
                self.display.show_current_weather(weather_data)
                self.display.show_forecast(weather_data)
            else:
                logger.error("Weather data could not be retrieved")
                print("Could not retrieve weather data. Please check your input or connection.")
        except KeyboardInterrupt:
            logger.info("Application terminated by user")
            print("\nApplication terminated by user.")
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
            print("Please check the log for more information.")
