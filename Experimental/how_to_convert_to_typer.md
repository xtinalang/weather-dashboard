To convert this weather application to work with Typer, you'll need to restructure it to use Typer's command-line interface functionality. Typer is a library for building CLI applications that's built on top of Click, but with better type hints and a more intuitive API.

Here's how you can modify your weather app to work with Typer:

The key changes made to convert your weather app to work with Typer include:

1. **Added Typer imports and created a Typer app instance**: `app = typer.Typer(help="Weather CLI App")`

2. **Converted print statements to Typer's echo function**: `typer.echo()` instead of `print()`

3. **Created separate command functions** with the `@app.command()` decorator:
   - `search`: To search for locations
   - `current`: To get current weather information
   - `forecast`: To get the 7-day forecast
   - `full`: To get both current weather and forecast

4. **Added type hints** throughout the code to take advantage of Typer's strong typing features

5. **Implemented command-line options and arguments**:
   - Added `--location`/`-l` options to specify the location directly
   - Added `--search`/`-s` flag to search for a location first
   - Used `typer.Argument` and `typer.Option` for command parameters

6. **Added help text** for the app, commands, and options

7. **Used Typer's interactive prompts** with `typer.prompt()` instead of `input()`

8. **Added error handling** with `typer.Exit()` where appropriate


```python
import typer # new Module
import requests
import re
from typing import Optional #new Module
from decouple import config


class WeatherAPI:
    def __init__(self, api_key=None):
        self.api_key = config("WEATHER_API_KEY")
        self.base_url = config("BASE_URL")
        self.search_url = config("SEARCH_URL")
        self.forcast_url = config("FORCAST_URL")
    
    def get_weather(self, location: str):
        """Get weather data from weatherapi.com for a given location"""
        try:
            params = {
                "q": location,
                "key": self.api_key,
                "days": 7,  # Get 7-day forecast
                "aqi": "yes"  # Include air quality data
            }
            response = requests.get(f"{self.forcast_url}", params=params)
            response.raise_for_status()
            weather_data = response.json()
            
            if "error" in weather_data:
                typer.echo(f"API error: {weather_data['error']['message']}")
                return None
                
            return weather_data
        except requests.exceptions.RequestException as e:
            typer.echo(f"Request error: {e}")
            return None
        except Exception as e:
            typer.echo(f"An unexpected error occurred: {e}")
            return None
    
    def search_city(self, query: str):
        """Search for city using weatherapi.com's search/autocomplete API"""
        try:
            params = {
                "q": query,
                "key": self.api_key,
            }
            response = requests.get(f"{self.search_url}", params=params)
            response.raise_for_status()
            location_data = response.json()
            
            if isinstance(location_data, dict) and "error" in location_data:
                typer.echo(f"API error: {location_data['error']['message']}")
                return None
                
            return location_data
        except requests.exceptions.RequestException as e:
            typer.echo(f"Request error: {e}")
            return None
        except Exception as e:
            typer.echo(f"An unexpected error occurred: {e}")
            return None


class WeatherDisplay:
    @staticmethod
    def get_weather_emoji(condition: str) -> str:
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
    def show_city(city: list):
        """Display found city"""
        if not city:
            typer.echo("No city found.")
            return
        
        typer.echo("\n📍 Found city:")
        typer.echo("=" * 50)
        
        for i, location in enumerate(city, 1):
            typer.echo(f"{i}. {location['name']}, {location.get('region', 'N/A')}, {location['country']}")
            typer.echo(f"   Lat: {location['lat']}, Lon: {location['lon']}")
            typer.echo(f"   URL: {location.get('url', 'N/A')}")
            typer.echo("-" * 50)
        
        return city

    @staticmethod
    def show_current_weather(weather_data: dict):
        """Display current weather information"""
        if not weather_data:
            typer.echo("❌ Could not retrieve weather data.")
            return

        location = weather_data["location"]
        current = weather_data["current"]
        condition_text = current['condition']['text']
        emoji = WeatherDisplay.get_weather_emoji(condition_text)

        typer.echo(f"\nWeather in 📍 {location['name']}, {location['region']}, {location['country']}:")
        typer.echo(f"{emoji} {condition_text}")
        typer.echo(f"🌡️ Temperature: {current['temp_c']}°C / {current['temp_f']}°F")
        typer.echo(f"🌡️ Feels like: {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        typer.echo(f"💧 Humidity: {current['humidity']}%")
        typer.echo(f"💨 Wind: {current['wind_kph']} kph / {current['wind_mph']} mph, {current['wind_dir']}")
        typer.echo(f"🌫️ Visibility: {current['vis_km']} km / {current['vis_miles']} miles")
        typer.echo(f"📊 Pressure: {current['pressure_mb']} mb / {current['pressure_in']} in")
        typer.echo(f"☔ Precipitation: {current['precip_mm']} mm / {current['precip_in']} in")
        typer.echo(f"🔄 Last updated: {current['last_updated']}")
    
    @staticmethod
    def show_forecast(weather_data: dict):
        """Display forecast information"""
        if not weather_data or "forecast" not in weather_data:
            return
        
        forecast = weather_data["forecast"]["forecastday"]
        
        typer.echo("\n🗓️ 7-Day Weather Forecast:")
        typer.echo("=" * 40)
        
        for day in forecast:
            date = day["date"]
            day_data = day["day"]
            astro = day["astro"]
            
            condition_text = day_data['condition']['text']
            emoji = WeatherDisplay.get_weather_emoji(condition_text)
            
            typer.echo(f"\n📅 Date: {date}")
            typer.echo(f"{emoji} {condition_text}")
            typer.echo(f"🌡️ Max: {day_data['maxtemp_c']}°C / {day_data['maxtemp_f']}°F")
            typer.echo(f"🌡️ Min: {day_data['mintemp_c']}°C / {day_data['mintemp_f']}°F")
            typer.echo(f"☔ Chance of rain: {day_data['daily_chance_of_rain']}%")
            typer.echo(f"❄️ Chance of snow: {day_data['daily_chance_of_snow']}%")
            typer.echo(f"🌄 Sunrise: {astro['sunrise']} | 🌇 Sunset: {astro['sunset']}")
            typer.echo("-" * 40)


# Initialize Typer app
app = typer.Typer(help="Weather CLI App - Get weather information for locations worldwide")
weather_api = WeatherAPI()
display = WeatherDisplay()


@app.command() # to imply this command will be used in Typer
def search(query: str = typer.Argument(..., help="Search query for location")):
    """Search for locations by name, region, etc."""
    typer.echo(f"Searching for '{query}'...")
    city = weather_api.search_city(query)
    
    if not city:
        typer.echo("No city found. Please try a different search term.")
        raise typer.Exit(code=1)
    
    cities = display.show_city(city)
    
    # Let user select a location
    selection = typer.prompt("Select a location (number)", default="1")
    try:
        selection_idx = int(selection) - 1
        if 0 <= selection_idx < len(cities):
            selected_location = cities[selection_idx]
            typer.echo(f"Selected: {selected_location['name']}, {selected_location.get('region', '')}, {selected_location['country']}")
            return f"{selected_location['lat']},{selected_location['lon']}"
        else:
            typer.echo(f"Please enter a number between 1 and {len(cities)}.")
            raise typer.Exit(code=1)
    except ValueError:
        typer.echo("Please enter a valid number.")
        raise typer.Exit(code=1)


@app.command()
def current(
    location: str = typer.Option(None, "--location", "-l", help="Location (city name, zip, lat,lon)"),
    search_first: bool = typer.Option(False, "--search", "-s", help="Search for location first")
):
    """Get current weather information"""
    # Handle searching first if requested
    if search_first:
        query = typer.prompt("Search for a location")
        location = search(query)
    
    # If location is still None, prompt for it
    if location is None:
        location = typer.prompt("Enter location (city name, zip, lat,lon)")
    
    typer.echo(f"Fetching current weather for {location}...")
    weather_data = weather_api.get_weather(location)
    
    if weather_data:
        display.show_current_weather(weather_data)
    else:
        typer.echo("Failed to get weather data.")
        raise typer.Exit(code=1)


@app.command()
def forecast(
    location: str = typer.Option(None, "--location", "-l", help="Location (city name, zip, lat,lon)"),
    search_first: bool = typer.Option(False, "--search", "-s", help="Search for location first")
):
    """Get 7-day forecast"""
    # Handle searching first if requested
    if search_first:
        query = typer.prompt("Search for a location")
        location = search(query)
    
    # If location is still None, prompt for it
    if location is None:
        location = typer.prompt("Enter location (city name, zip, lat,lon)")
    
    typer.echo(f"Fetching forecast for {location}...")
    weather_data = weather_api.get_weather(location)
    
    if weather_data:
        display.show_forecast(weather_data)
    else:
        typer.echo("Failed to get weather data.")
        raise typer.Exit(code=1)


@app.command()
def full(
    location: str = typer.Option(None, "--location", "-l", help="Location (city name, zip, lat,lon)"),
    search_first: bool = typer.Option(False, "--search", "-s", help="Search for location first")
):
    """Get both current weather and forecast"""
    # Handle searching first if requested
    if search_first:
        query = typer.prompt("Search for a location")
        location = search(query)
    
    # If location is still None, prompt for it
    if location is None:
        location = typer.prompt("Enter location (city name, zip, lat,lon)")
    
    typer.echo(f"Fetching weather data for {location}...")
    weather_data = weather_api.get_weather(location)
    
    if weather_data:
        display.show_current_weather(weather_data)
        display.show_forecast(weather_data)
    else:
        typer.echo("Failed to get weather data.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

```

The key changes made to convert your weather app to work with Typer include:

1. **Added Typer imports and created a Typer app instance**: `app = typer.Typer(help="Weather CLI App")`

2. **Converted print statements to Typer's echo function**: `typer.echo()` instead of `print()`

3. **Created separate command functions** with the `@app.command()` decorator:
   - `search`: To search for locations
   - `current`: To get current weather information
   - `forecast`: To get the 7-day forecast
   - `full`: To get both current weather and forecast

4. **Added type hints** throughout the code to take advantage of Typer's strong typing features

5. **Implemented command-line options and arguments**:
   - Added `--location`/`-l` options to specify the location directly
   - Added `--search`/`-s` flag to search for a location first
   - Used `typer.Argument` and `typer.Option` for command parameters

6. **Added help text** for the app, commands, and options

7. **Used Typer's interactive prompts** with `typer.prompt()` instead of `input()`

8. **Added error handling** with `typer.Exit()` where appropriate

This structure makes the weather app more user-friendly as a command-line tool. Users can now run commands like:

```
# Search for a location
python weather_app.py search "New York"

# Get current weather for a location
python weather_app.py current --location "London"

# Get forecast with interactive search
python weather_app.py forecast --search

# Get full weather information (current + forecast)
python weather_app.py full --location "Tokyo"
```
# How to run typer_weather_app
1. Show help
```python
typer typer_weather_app.py run --help
```
2. Run search
```python
typer typer_weather_app.py run search <city>
```
3. Run current 
```python
typer typer_weather_app.py run current
```
4. Run forcast
```python
typer typer_weather_app.py run forecast
```
5. Run full
```python
typer typer_weather_app.py run full
```