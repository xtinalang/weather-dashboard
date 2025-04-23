import requests
import re
from decouple import config

API_KEY = config("WEATHER_API_KEY")

# Fetch actual states in the US 
def fetch_us_states(url="https://gist.githubusercontent.com/mshafrir/2646763/raw/states_titlecase.json"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        states_data = response.json()
        return set(state["name"] for state in states_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching states: {e}")
        return set()

# Validates City/State for US
def validate_city_state_input(city_state_input, valid_states):
    parts = [part.strip() for part in city_state_input.split(',')]
    if len(parts) != 2:
        return False, "Please enter city and state separated by a comma. (e.g., Austin, Texas)"

    city, state = parts
    city_pattern = re.compile(r"^[a-zA-Z\s\-.']+$")

    if not city or not city_pattern.match(city):
        return False, "Invalid city format."

    if state.title() not in valid_states:
        return False, f"'{state}' is not a recognized U.S. state."

    return True, (city, state.title())

# Task to get city name from user 
def get_city_name():
    us_states = fetch_us_states()
    if not us_states:
        return None, None

    while True:
        city_state = input("Please enter city and state (e.g., Seattle, Washington): ")
        valid, result = validate_city_state_input(city_state, us_states)
        if valid:
            print("City and state accepted!")
            return result
        else:
            print(f"Error: {result}")

# Use city name to get current weather via API from weatherapi.com
def get_weather(city): 
    try: 
        base_url = "http://api.weatherapi.com/v1/forecast.json"
        params = {"q": city, "key": API_KEY, "units": "metric"}
        response = requests.get(base_url, params=params)
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
def get_weather_emoji(condition):
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

def show_weather(weather_data):
    if weather_data:
        location = weather_data["location"]
        current = weather_data["current"]
        condition_text = current['condition']['text']
        emoji = get_weather_emoji(condition_text)

        print(f"\nWeather in 📍 {location['name']}, {location['region']}, {location['country']}:")
        print(f"{emoji} {condition_text}")
        print(f"🌡️ Temperature: {current['temp_c']}°C")
        print(f"💧 Humidity: {current['humidity']}%")
        print(f"💨 Wind: {current['wind_kph']} kph")
    else:
        print("❌ Could not retrieve weather data.")

if __name__ == "__main__":
    city, state = get_city_name()
    if city and state:
        print(f"You entered: City = {city}, State = {state}")
        full_location = f"{city}, {state}"
        current_weather = get_weather(full_location)
        show_weather(current_weather)