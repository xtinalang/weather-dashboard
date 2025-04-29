from user_input import User_Input_Information
from weather_api import WeatherAPI
from weather_display import WeatherDisplay
import logging

logger = logging.getLogger("weather_app")

class LocationManager:
    def __init__(self, weather_api: WeatherAPI, display: WeatherDisplay):
        self.weather_api = weather_api
        self.display = display
        self.user_input = User_Input_Information()

    def get_location(self) -> str:
        while True:
            method = self.user_input.get_location_method()
            if method == "1":
                return self._search_location()
            elif method == "2":
                return self._direct_location()

    def _search_location(self) -> str:
        while True:
            query = self.user_input.get_search_query()
            city_list = self.weather_api.search_city(query)
            if not city_list:
                continue
            self.display.show_city(city_list)
            selection = self.user_input.get_location_selection(len(city_list))
            if selection.isdigit():
                idx = int(selection) - 1
                selected = city_list[idx]
                return f"{selected['lat']},{selected['lon']}"

    def _direct_location(self) -> str:
        while True:
            location = self.user_input.get_direct_location()
            results = self.weather_api.search_city(location)
            if results:
                self.display.show_city(results)
                return f"{results[0]['lat']},{results[0]['lon']}"
