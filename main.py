import requests
import re
from decouple import config


class WeatherAPI:
    def __init__(self, api_key=None):
        self.api_key = config("WEATHER_API_KEY")
        self.base_url = config("BASE_URL")
        self.search_url = config("SEARCH_URL")
        self.forcast_url = config("FORCAST_URL")
    
    def get_weather(self, location): ##Need to add hints
        """Get weather data from weatherapi.com for a given location"""
        try:
            params = {
                "q": location,
                "key": self.api_key,
                "days": 7,  # Get 7-day forecast
                "aqi": "yes"  # Include air quality data
            }
            response = requests.get(f"{self.forcast_url}", params=params) #uses constant from env file
            response.raise_for_status()
            weather_data = response.json()
            
            if "error" in weather_data:
                print(f"API error: {weather_data['error']['message']}")
                return None
                
            return weather_data
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
    
    def search_city(self, query):
        """Search for city using weatherapi.com's search/autocomplete API"""
        try:
            params = {
                "q": query,
                "key": self.api_key,
               # "city": location_data
            }
            response = requests.get(f"{self.search_url}", params=params)
            response.raise_for_status()
            location_data = response.json()
            
            if isinstance(location_data, dict) and "error" in location_data:
                print(f"API error: {location_data['error']['message']}")
                return None
                
            return location_data
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


class WeatherDisplay:
    @staticmethod
    def get_weather_emoji(condition):
        """Return an emoji matching the weather condition"""
        condition = condition.lower()
        if "sunny" in condition:
            return "☀️"
        elif "cloud" in condition:
            return "☁️"
        elif "rain" in condition or "drizzle" in condition:
            return "🌧️"
        elif "thunder" in condition:
            return "⛈️"
        elif "snow" in condition:
            return "❄️"
        elif "fog" in condition or "mist" in condition:
            return "🌫️"
        elif "clear" in condition:
            return "🌕"
        elif "wind" in condition:
            return "🌬️"
        else:
            return "🌈"  # Default cute fallback

    @staticmethod
    def show_city(city):
        """Display found city"""
        if not city:
            print("No city found.")
            return
        
        print("\n📍 Found city:")
        print("=" * 50)
        
        for i, location in enumerate(city, 1):
            print(f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}")
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            print(f"   URL: {location.get('url', 'N/A')}")
            print("-" * 50)

    @staticmethod
    def show_current_weather(weather_data):
        """Display current weather information"""
        if not weather_data:
            print("❌ Could not retrieve weather data.")
            return

        location = weather_data["location"]
        current = weather_data["current"]
        condition_text = current['condition']['text']
        emoji = WeatherDisplay.get_weather_emoji(condition_text)

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
    def show_forecast(weather_data):
        """Display forecast information"""
        if not weather_data or "forecast" not in weather_data:
            return
        
        forecast = weather_data["forecast"]["forecastday"]
        
        print("\n🗓️ 7-Day Weather Forecast:")
        print("=" * 40)
        
        for day in forecast:
            date = day["date"]
            day_data = day["day"]
            astro = day["astro"]
            
            condition_text = day_data['condition']['text']
            emoji = WeatherDisplay.get_weather_emoji(condition_text)
            
            print(f"\n📅 Date: {date}")
            print(f"{emoji} {condition_text}")
            print(f"🌡️ Max: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
            print(f"🌡️ Min: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
            print(f"☔ Chance of rain: {day_data['daily_chance_of_rain']}%")
            print(f"❄️ Chance of snow: {day_data['daily_chance_of_snow']}%")
            print(f"🌄 Sunrise: {astro['sunrise']} | 🌇 Sunset: {astro['sunset']}")
            print("-" * 40)


class WeatherApp:
    def __init__(self):
        self.weather_api = WeatherAPI()
        self.display = WeatherDisplay()
    
    def search_and_select_location(self):
        """Search for city and let user select one"""
        while True:
            search_query = input("Search for a location (city, region, etc.): ")
            if not search_query.strip():
                print("Please enter a valid search term.")
                continue
                
            print(f"Searching for '{search_query}'...")
            city = self.weather_api.search_city(search_query)
            
            if not city:
                print("No city found. Please try a different search term.")
                continue
                
            self.display.show_city(city)
            
            # Let user select a location
            while True:
                try:
                    selection = input(f"Select a location (1-{len(city)}) or 'q' to search again: ")
                    if selection.lower() == 'q':
                        break
                        
                    selection_idx = int(selection) - 1
                    if 0 <= selection_idx < len(city):
                        selected_location = city[selection_idx]
                        # Return the lat,lon as the query string for most accurate results
                        return f"{selected_location['lat']},{selected_location['lon']}"
                    else:
                        print(f"Please enter a number between 1 and {len(city)}.")
                except ValueError:
                    print("Please enter a valid number or 'q'.")
    
    def get_location_input(self):
        """Get location input from user with options"""
        print("\nHow would you like to specify the location?")
        print("1. Search for a location")
        print("2. Enter location directly (city name, zip code, lat,lon, etc.)")
    
        while True:
            choice = input("Enter your choice (1-2): ")
            if choice == "1":
                return self.search_and_select_location()
            elif choice == "2":
                # Add verification loop for direct location entry
                while True:
                    location = input("Enter location: ")
                
                    if not location.strip():
                        print("Please enter a valid location.")
                        continue
                
                    # Verify the location exists using the search_city method
                    verification_results = self.weather_api.search_city(location.strip())
                
                    if verification_results and len(verification_results) > 0:
                        # Show the matched locations
                        print("\nVerified locations matching your entry:")
                        self.display.show_city(verification_results)
                    
                        # Ask if they want to use one of these or continue with original entry
                        choice = input("\nUse one of these locations? (y/n): ")
                    
                        if choice.lower() == 'y':
                            while True:
                                try:
                                    selection = input(f"Select a location (1-{len(verification_results)}) or 'q' to cancel: ")
                                    if selection.lower() == 'q':
                                     break
                                    
                                    selection_idx = int(selection) - 1
                                    if 0 <= selection_idx < len(verification_results):
                                        selected_location = verification_results[selection_idx]
                                        # Return the lat,lon as the query string for most accurate results
                                        return f"{selected_location['lat']},{selected_location['lon']}"
                                    else:
                                        print(f"Please enter a number between 1 and {len(verification_results)}.")
                                except ValueError:
                                    print("Please enter a valid number or 'q'.")
                        else:
                            # User wants to use their original entry
                            print(f"Using your original entry: {location}")
                            return location.strip()
                    else:
                        print("Could not verify this location with the weather service.")
                        retry = input("Would you like to try again? (y/n): ")
                        if retry.lower() != 'y':
                            print("Returning to location selection menu...")
                            break  # Break the inner loop to return to choice selection
            else:
                print("Invalid choice. Please enter 1 or 2.")
    
    def run(self):
        """Main application flow"""
        print("Welcome to the Weather App!")
        print("==========================")
        
        location = self.get_location_input()
        print(f"\nFetching weather data for selected location...")
        weather_data = self.weather_api.get_weather(location)
        
        self.display.show_current_weather(weather_data)
        self.display.show_forecast(weather_data)


if __name__ == "__main__":
    app = WeatherApp()
    app.run()