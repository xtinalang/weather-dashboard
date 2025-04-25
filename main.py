import requests
import re
import logging
from decouple import config
from typing import Optional, Dict, Any, List, Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("weather_app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("weather_app")


class User_Input_Information:
    """Handles all user input operations"""
    
    @staticmethod
    def get_search_query() -> str:
        """Get location search query from user"""
        search_query: str = input("Search for a location (city, region, etc.): ").strip()
        logger.debug(f"User entered search query: {search_query}")
        return search_query
    
    @staticmethod
    def get_location_selection(city_count: int) -> str:
        """Get location selection from user"""
        selection: str = input(f"Select a location (1-{city_count}) or 'q' to search again: ")
        logger.debug(f"User entered location selection: {selection}")
        return selection
    
    @staticmethod
    def get_location_method() -> str:
        """Get user's preferred method to specify location"""
        print("\nHow would you like to specify the location?")
        print("1. Search for a location")
        print("2. Enter location directly (city name, zip code, lat,lon, etc.)")
        
        choice: str = input("Enter your choice (1-2): ")
        logger.debug(f"User selected location method: {choice}")
        return choice
    
    @staticmethod
    def get_direct_location() -> str:
        """Get direct location input from user"""
        location: str = input("Enter location: ").strip()
        logger.debug(f"User entered direct location: {location}")
        return location
    
    @staticmethod
    def confirm_verified_locations() -> str:
        """Ask user if they want to use verified locations"""
        choice: str = input("\nUse one of these locations? (y/n): ").lower()
        logger.debug(f"User confirmed verified locations: {choice}")
        return choice
    
    @staticmethod
    def get_verified_location_selection(locations_count: int) -> str:
        """Get verified location selection from user"""
        selection: str = input(f"Select a location (1-{locations_count}) or 'q' to cancel: ")
        logger.debug(f"User entered verified location selection: {selection}")
        return selection
    
    @staticmethod
    def confirm_retry() -> str:
        """Ask user if they want to retry location entry"""
        retry: str = input("Would you like to try again? (y/n): ").lower()
        logger.debug(f"User confirmed retry: {retry}")
        return retry


class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None) -> None:
        logger.debug("Initializing WeatherAPI")
        self.api_key: str = api_key or config("WEATHER_API_KEY")
        self.base_url: str = config("BASE_URL")  # Need to just put as static
        self.search_url: str = f"{self.base_url}/search.json"
        self.forecast_url: str = f"{self.base_url}/forecast.json"
        logger.debug(f"Base URL set to: {self.base_url}")
    
    def get_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Get weather data from weatherapi.com for a given location"""
        logger.info(f"Getting weather data for location: {location}")
        try:
            params: Dict[str, Any] = {
                "q": location,
                "key": self.api_key,
                "days": 7,  # Get 7-Day forcast
                "aqi": "yes"  # Include Air quality Data
            }
            logger.debug(f"Making API request to {self.forecast_url}")
            response = requests.get(f"{self.forecast_url}", params=params)
            response.raise_for_status()
            weather_data: Dict[str, Any] = response.json()
            
            if "error" in weather_data:
                logger.error(f"API error: {weather_data['error']['message']}")
                print(f"API error: {weather_data['error']['message']}")
                return None
                
            logger.debug("Weather data successfully retrieved")
            return weather_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}", exc_info=True)
            print(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
            return None
    
    def search_city(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search for city using weatherapi.com's search/autocomplete API"""
        logger.info(f"Searching for city: {query}")
        try:
            params: Dict[str, str] = {
                "q": query,
                "key": self.api_key,
               # "city": location_data
            }
            logger.debug(f"Making API request to {self.search_url}")
            response = requests.get(f"{self.search_url}", params=params)
            response.raise_for_status()
            location_data: List[Dict[str, Any]] = response.json()
            
            if isinstance(location_data, dict) and "error" in location_data:
                logger.error(f"API error: {location_data['error']['message']}")
                print(f"API error: {location_data['error']['message']}")
                return None
                
            logger.debug(f"Found {len(location_data)} locations")
            return location_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}", exc_info=True)
            print(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
            return None


class WeatherDisplay:
    def __init__(self) -> None:
        logger.debug("Initializing WeatherDisplay")
        
    @staticmethod
    def get_weather_emoji(condition: str) -> str:
        """Return an emoji matching the weather condition"""
        logger.debug(f"Getting emoji for condition: {condition}")
        condition = condition.lower()
        emoji_map: Dict[str, str] = {
            "sunny": "☀️",
            "cloud": "☁️",
            "rain": "🌧️",
            "drizzle": "🌧️",
            "thunder": "⛈️",
            "snow": "❄️",
            "fog": "🌫️",
            "mist": "🌫️",
            "clear": "🌕",
            "wind": "🌬️"
        }
        
        for key, emoji in emoji_map.items():
            if key in condition:
                logger.debug(f"Found matching emoji: {emoji} for condition: {condition}")
                return emoji
        logger.debug(f"No specific emoji found for {condition}, using default")
        return "🌈"  # Default cute fallback

    @staticmethod
    def show_city(city: Optional[List[Dict[str, Any]]]) -> None:
        """Display found city"""
        logger.info("Displaying city information")
        if not city:
            logger.warning("No city data to display")
            print("No city found.")
            return
        
        print("\n📍 Found city:")
        print("=" * 50)
        
        for i, location in enumerate(city, 1):
            logger.debug(f"Displaying location {i}: {location['name']}")
            print(f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}")
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            print(f"   URL: {location.get('url', 'N/A')}")
            print("-" * 50)

    @staticmethod
    def show_current_weather(weather_data: Optional[Dict[str, Any]]) -> None:
        """Display current weather information"""
        logger.info("Displaying current weather information")
        if not weather_data:
            logger.warning("No weather data to display")
            print("❌ Could not retrieve weather data.")
            return

        location: Dict[str, Any] = weather_data["location"]
        current: Dict[str, Any] = weather_data["current"]
        condition_text: str = current['condition']['text']
        emoji: str = WeatherDisplay.get_weather_emoji(condition_text)

        logger.debug(f"Displaying weather for {location['name']}")
        print(f"\nWeather in 📍 {location['name']}, {location['region']}, {location['country']}:")
        print(f"{emoji} {condition_text}")
        print(f"🌡️ Temperature: {current['temp_c']}°C / {current['temp_f']}°F")
        print(f"🌡️ Feels like: {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        print(f"💧 Humidity: {current['humidity']}%")
        print(f"💨 Wind: {current['wind_kph']} kph / {current['wind_mph']} mph, {current['wind_dir']}")
        print(f"🌫️ Visibility: {current['vis_km']} km / {current['vis_miles']} miles")
        print(f"📊 Pressure: {current['pressure_mb']} mb / {current['pressure_in']} in")
        print(f"☔ Precipitation: {current['precip_mm']} mm / {current['precip_in']} in")
        print(f"🔄 Last updated: {current['last_updated']}")
    
    @staticmethod
    def show_forecast(weather_data: Optional[Dict[str, Any]]) -> None:
        """Display forecast information"""
        logger.info("Displaying forecast information")
        if not weather_data or "forecast" not in weather_data:
            logger.warning("No forecast data to display")
            return
        
        forecast: List[Dict[str, Any]] = weather_data["forecast"]["forecastday"]
        logger.debug(f"Displaying forecast for {len(forecast)} days")
        
        print("\n🗓️ 7-Day Weather Forecast:")
        print("=" * 40)
        
        for day in forecast:
            date: str = day["date"]
            day_data: Dict[str, Any] = day["day"]
            astro: Dict[str, str] = day["astro"]
            
            condition_text: str = day_data['condition']['text']
            emoji: str = WeatherDisplay.get_weather_emoji(condition_text)
            
            logger.debug(f"Displaying forecast for date: {date}")
                      
            print(f"\n📅 Date: {date}")
            print(f"{emoji} {condition_text}")
            print(f"🌡️ Max: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
            print(f"🌡️ Min: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
            print(f"☔ Chance of rain: {day_data['daily_chance_of_rain']}%")
            print(f"❄️ Chance of snow: {day_data['daily_chance_of_snow']}%")
            print(f"🌄 Sunrise: {astro['sunrise']} | 🌇 Sunset: {astro['sunset']}")
            print("-" * 40)


class LocationManager:
    """Handles location search and selection operations"""
    
    def __init__(self, weather_api: WeatherAPI, display: WeatherDisplay) -> None:
        self.weather_api = weather_api
        self.display = display
        self.user_input = User_Input_Information()
        logger.debug("Initializing LocationManager")
    
    def search_and_select_location(self) -> str:
        """Search for city and let user select one"""
        logger.info("Starting location search")
        while True:
            search_query = self.user_input.get_search_query()
            if not search_query:
                logger.warning("Empty search query entered")
                print("Please enter a valid search term.")
                continue
                
            logger.info(f"Searching for '{search_query}'")
            print(f"Searching for '{search_query}'...")
            city = self.weather_api.search_city(search_query)
            
            if not city:
                logger.warning("No city found for the search query")
                print("No city found. Please try a different search term.")
                continue
                
            self.display.show_city(city)
            
            # Let user select a location
            while True:
                try:
                    selection = self.user_input.get_location_selection(len(city))
                    if selection.lower() == 'q':
                        logger.debug("User chose to search again")
                        break
                        
                    selection_idx: int = int(selection) - 1
                    if 0 <= selection_idx < len(city):
                        selected_location: Dict[str, Any] = city[selection_idx]
                        location_str = f"{selected_location['lat']},{selected_location['lon']}"
                        logger.info(f"User selected location: {selected_location['name']} ({location_str})")
                        # Return the lat,lon as the query string for most accurate results
                        return location_str
                    else:
                        logger.warning(f"Invalid selection index: {selection_idx}")
                        print(f"Please enter a number between 1 and {len(city)}.")
                except ValueError:
                    logger.error("Invalid selection input", exc_info=True)
                    print("Please enter a valid number or 'q'.")
    
    def handle_direct_location_entry(self) -> str:
        """Handle direct location entry and verification"""
        logger.info("Handling direct location entry")
        while True:
            location = self.user_input.get_direct_location()
            
            if not location:
                logger.warning("Empty location entered")
                print("Please enter a valid location.")
                continue
            
            # Verify the location exists using the search_city method
            logger.info(f"Verifying location: {location}")
            verification_results = self.weather_api.search_city(location)
            
            if verification_results and len(verification_results) > 0:
                # Show the matched locations
                logger.info(f"Found {len(verification_results)} matching locations")
                print("\nVerified locations matching your entry:")
                self.display.show_city(verification_results)
                
                # Ask if they want to use one of these or continue with original entry
                choice = self.user_input.confirm_verified_locations()
                
                if choice == 'y':
                    while True:
                        try:
                            selection = self.user_input.get_verified_location_selection(len(verification_results))
                            if selection.lower() == 'q':
                                logger.debug("User cancelled selection")
                                break
                            
                            selection_idx: int = int(selection) - 1
                            if 0 <= selection_idx < len(verification_results):
                                selected_location: Dict[str, Any] = verification_results[selection_idx]
                                location_str = f"{selected_location['lat']},{selected_location['lon']}"
                                logger.info(f"User selected verified location: {selected_location['name']} ({location_str})")
                                # Return the lat,lon as the query string for most accurate results
                                return location_str
                            else:
                                logger.warning(f"Invalid selection index: {selection_idx}")
                                print(f"Please enter a number between 1 and {len(verification_results)}.")
                        except ValueError:
                            logger.error("Invalid selection input", exc_info=True)
                            print("Please enter a valid number or 'q'.")
                else:
                    # User wants to use their original entry
                    logger.info(f"User chose to use original entry: {location}")
                    print(f"Using your original entry: {location}")
                    return location
            else:
                logger.warning(f"Could not verify location: {location}")
                print("Could not verify this location with the weather service.")
                retry = self.user_input.confirm_retry()
                if retry != 'y':
                    logger.debug("User chose not to retry location entry")
                    print("Returning to location selection menu...")
                    break  # Break the inner loop to return to choice selection
        
        return ""  # Return empty string to signal no location selected

    def get_location(self) -> str:
        """Get location from user with options"""
        logger.info("Getting location from user")
        
        while True:
            choice = self.user_input.get_location_method()
            
            if choice == "1":
                logger.info("User chose to search for a location")
                location = self.search_and_select_location()
                if location:
                    return location
            elif choice == "2":
                logger.info("User chose to enter location directly")
                location = self.handle_direct_location_entry()
                if location:
                    return location
            else:
                logger.warning(f"Invalid choice: {choice}")
                print("Invalid choice. Please enter 1 or 2.")


class WeatherApp:
    def __init__(self) -> None:
        logger.info("Initializing Weather App")
        self.weather_api: WeatherAPI = WeatherAPI()
        self.display: WeatherDisplay = WeatherDisplay()
        self.location_manager: LocationManager = LocationManager(self.weather_api, self.display)
    
    def run(self) -> None:
        """Main application flow"""
        logger.info("Starting Weather App")
        print("Welcome to the Weather App!")
        print("==========================")
        
        try:
            location: str = self.location_manager.get_location()
            if not location:
                logger.warning("No location selected")
                print("No location selected. Exiting application.")
                return
                
            logger.info(f"Selected location: {location}")
            print(f"\nFetching weather data for selected location...")
            weather_data: Optional[Dict[str, Any]] = self.weather_api.get_weather(location)
            
            if weather_data:
                logger.info("Successfully retrieved weather data")
                self.display.show_current_weather(weather_data)
                self.display.show_forecast(weather_data)
            else:
                logger.error("Failed to retrieve weather data")
                print("Could not retrieve weather data. Please check your internet connection and try again.")
        except KeyboardInterrupt:
            logger.info("Application terminated by user")
            print("\nApplication terminated by user.")
        except Exception as e:
            logger.critical(f"Unexpected error in main application flow: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
            print("Check the log file for more details.")


if __name__ == "__main__":
    try:
        logger.info("===== Weather App Started =====")
        app: WeatherApp = WeatherApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error occurred: {e}")
    finally:
        logger.info("===== Weather App Finished =====")