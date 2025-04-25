import requests
from decouple import config

class WeatherApp:
    def __init__(self):
        # Consolidate API and display into a single class
        self.api_key = config("WEATHER_API_KEY")
        self.base_url = config("BASE_URL")
        self.search_url = config("SEARCH_URL")
        self.forcast_url = config("FORCAST_URL")
    
    def get_weather_emoji(self, condition):
        """Return an emoji matching the weather condition"""
        condition = condition.lower()
        
        # Using dictionary instead of if/elif chain
        condition_emojis = {
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
        
        # Check for matching condition
        for key, emoji in condition_emojis.items():
            if key in condition:
                return emoji
                
        return "🌈"  # Default cute fallback
    
    def api_request(self, url, params):
        """Centralized API request handler"""
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and "error" in data:
                print(f"API error: {data['error']['message']}")
                return None
                
            return data
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
    
    def search_city(self, query):
        """Search for city using weatherapi.com's search/autocomplete API"""
        params = {
            "q": query,
            "key": self.api_key
        }
        return self.api_request(self.search_url, params)
    
    def get_weather(self, location):
        """Get weather data from weatherapi.com for a given location"""
        params = {
            "q": location,
            "key": self.api_key,
            "days": 7,
            "aqi": "yes"
        }
        return self.api_request(self.forcast_url, params)
    
    def display_cities(self, cities):
        """Display found cities"""
        if not cities:
            print("No city found.")
            return False
        
        print("\n📍 Found city:")
        print("=" * 50)
        
        for i, location in enumerate(cities, 1):
            print(f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}")
            print(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            print(f"   URL: {location.get('url', 'N/A')}")
            print("-" * 50)
        return True
    
    def select_city(self, cities, prompt="Select a location"):
        """Let user select a city from list"""
        while True:
            try:
                selection = input(f"{prompt} (1-{len(cities)}) or 'q' to cancel: ")
                if selection.lower() == 'q':
                    return None
                    
                selection_idx = int(selection) - 1
                if 0 <= selection_idx < len(cities):
                    return cities[selection_idx]
                else:
                    print(f"Please enter a number between 1 and {len(cities)}.")
            except ValueError:
                print("Please enter a valid number or 'q'.")
    
    def get_location(self):
        """Combined location input handling"""
        print("\nHow would you like to specify the location?")
        print("1. Search for a location")
        print("2. Enter location directly (city name, zip code, lat,lon, etc.)")
        
        while True:
            choice = input("Enter your choice (1-2): ")
            
            # OPTION 1: Search and select
            if choice == "1":
                while True:
                    search_query = input("Search for a location (city, region, etc.) or 'q' to go back: ")
                    if search_query.lower() == 'q':
                        break
                        
                    if not search_query.strip():
                        print("Please enter a valid search term.")
                        continue
                        
                    print(f"Searching for '{search_query}'...")
                    cities = self.search_city(search_query)
                    
                    if self.display_cities(cities):
                        selected = self.select_city(cities)
                        if selected:
                            return f"{selected['lat']},{selected['lon']}"
            
            # OPTION 2: Direct entry with verification
            elif choice == "2":
                while True:
                    location = input("Enter location or 'q' to go back: ")
                    if location.lower() == 'q':
                        break
                        
                    if not location.strip():
                        print("Please enter a valid location.")
                        continue
                    
                    # Verify the location
                    cities = self.search_city(location.strip())
                    
                    if cities and len(cities) > 0:
                        print("\nVerified locations matching your entry:")
                        self.display_cities(cities)
                        
                        use_verified = input("\nUse one of these locations? (y/n): ").lower()
                        if use_verified == 'y':
                            selected = self.select_city(cities)
                            if selected:
                                return f"{selected['lat']},{selected['lon']}"
                        else:
                            print(f"Using your original entry: {location}")
                            return location.strip()
                    else:
                        print("Could not verify this location with the weather service.")
                        retry = input("Would you like to try again? (y/n): ")
                        if retry.lower() != 'y':
                            break
            else:
                print("Invalid choice. Please enter 1 or 2.")
    
    def display_weather(self, weather_data):
        """Display both current weather and forecast"""
        if not weather_data:
            print("❌ Could not retrieve weather data.")
            return

        # Display current weather
        location = weather_data["location"]
        current = weather_data["current"]
        condition_text = current['condition']['text']
        emoji = self.get_weather_emoji(condition_text)

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
        
        # Display forecast
        if "forecast" in weather_data:
            forecast = weather_data["forecast"]["forecastday"]
            
            print("\n🗓️ 7-Day Weather Forecast:")
            print("=" * 40)
            
            for day in forecast:
                date = day["date"]
                day_data = day["day"]
                astro = day["astro"]
                
                condition_text = day_data['condition']['text']
                emoji = self.get_weather_emoji(condition_text)
                
                print(f"\n📅 Date: {date}")
                print(f"{emoji} {condition_text}")
                print(f"🌡️ Max: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
                print(f"🌡️ Min: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
                print(f"☔ Chance of rain: {day_data['daily_chance_of_rain']}%")
                print(f"❄️ Chance of snow: {day_data['daily_chance_of_snow']}%")
                print(f"🌄 Sunrise: {astro['sunrise']} | 🌇 Sunset: {astro['sunset']}")
                print("-" * 40)
    
    def run(self):
        """Main application flow"""
        print("Welcome to the Weather App!")
        print("==========================")
        
        location = self.get_location()
        if location:
            print(f"\nFetching weather data for selected location...")
            weather_data = self.get_weather(location)
            self.display_weather(weather_data)
        else:
            print("\nNo location selected. Exiting application.")


if __name__ == "__main__":
    app = WeatherApp()
    app.run()