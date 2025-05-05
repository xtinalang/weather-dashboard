# weather-dashboard

## Will need to be re-written  

## 1. Overall Structure

The code is organized into three main classes:
- `WeatherAPI`: Handles all interactions with the weatherapi.com service
- `WeatherDisplay`: Handles formatting and displaying weather data
- `WeatherApp`: Orchestrates the entire application flow

This structure follows the principle of separation of concerns, where each class has a specific responsibility.

## 2. WeatherAPI Class

```python
class WeatherAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or config("WEATHER_API_KEY")
        self.base_url = "http://api.weatherapi.com/v1"
```

This class initializes with an API key (either provided directly or loaded from environment variables using the `config` function from the `decouple` library). It also sets the base URL for the API.

It has two main methods:

### get_weather()
```python
def get_weather(self, location):
    """Get weather data from weatherapi.com for a given location"""
    # ...code that makes an API request...
```
This method fetches weather and forecast data for a specified location. It:
- Creates a request to the `forecast.json` endpoint
- Includes parameters for the API key, location, forecast days, and air quality information
- Handles errors and returns the JSON response or None if there's an error

### search_locations()
```python
def search_locations(self, query):
    """Search for locations using weatherapi.com's search/autocomplete API"""
    # ...code that makes an API request...
```
This method searches for locations matching a query string. It:
- Makes a request to the `search.json` endpoint
- Returns a list of matching locations with details like name, region, country, and coordinates
- Handles errors appropriately

## 3. WeatherDisplay Class

This class contains static methods for displaying various types of data:

### get_weather_emoji()
```python
@staticmethod
def get_weather_emoji(condition):
    """Return an emoji matching the weather condition"""
    # ...code that maps weather conditions to emojis...
```
This method takes a weather condition text and returns a relevant emoji, making the output more visually appealing. ##Note: This may change in the future depending on the type of application. 

### show_locations()
```python
@staticmethod
def show_locations(locations):
    """Display found locations"""
    # ...code that prints location information...
```
This method displays a numbered list of locations with details like name, region, country, and coordinates.

### show_current_weather()
```python
@staticmethod
def show_current_weather(weather_data):
    """Display current weather information"""
    # ...code that prints current weather info...
```
This method formats and displays current weather information including temperature, humidity, wind, and more.

### show_forecast()
```python
@staticmethod
def show_forecast(weather_data):
    """Display forecast information"""
    # ...code that prints forecast info...
```
This method displays a 3-day weather forecast with details like temperature range, conditions, and sunrise/sunset times.

## 4. WeatherApp Class

This class coordinates the entire application flow:

### __init__()
```python
def __init__(self):
    self.weather_api = WeatherAPI()
    self.display = WeatherDisplay()
```
The constructor initializes instances of the `WeatherAPI` and `WeatherDisplay` classes.

### search_and_select_location()
```python
def search_and_select_location(self):
    """Search for locations and let user select one"""
    # ...code that handles search and selection...
```
This method:
1. Prompts the user for a search term
2. Calls the API to search for matching locations
3. Displays the results
4. Lets the user select a location from the results
5. Returns the latitude and longitude of the selected location

### get_location_input()
```python
def get_location_input(self):
    """Get location input from user with options"""
    # ...code that offers input options...
```
This method gives the user two options:
1. Search for a location using the search functionality
2. Enter a location directly (city name, zip code, coordinates)

### run()
```python
def run(self):
    """Main application flow"""
    # ...code that runs the main app logic...
```
This method orchestrates the main application flow:
1. Welcomes the user
2. Gets location input
3. Fetches weather data
4. Displays current weather and forecast

## 5. Main Execution

```python
if __name__ == "__main__":
    app = WeatherApp()
    app.run()
```

This part ensures that the application runs only when executed directly (not when imported as a module). It creates an instance of the `WeatherApp` class and calls its `run()` method.

## Key Features of the Code

1. **Error Handling**: The code includes comprehensive error handling for API requests and user input.

2. **User Experience**: The application provides a friendly interface with emojis and formatted output.

3. **Flexibility**: Users can search for locations or enter them directly.

4. **Comprehensive Data**: The app displays detailed weather information and forecasts.

5. **Modularity**: The code is organized into classes with specific responsibilities, making it easier to maintain and extend.

To use this code, you would need:
1. An API key from weatherapi.com
2. The Python `requests` and `decouple` libraries installed
3. Your API key stored in an environment variable or .env file that the `decouple` library can access

Would you like me to explain any specific part of the code in more detail?