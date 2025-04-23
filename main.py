import requests
import os
from decouple import config

API_KEY = config("WEATHER_API_KEY")


##TASK TO GET CITY NAME FROM USER 
## NEED TO ADD ERRORS like not a city
def get_city_name ():
    city = input("Please enter city. ")
    return city


### USE CITY NAME TO GET CURRENT WEATHER VIA API FROM WEATHERAPI.COM
def get_weather(city): 
    try: 
        base_url = "http://api.weatherapi.com/v1/forecast.json"
        params = {"q": city, "key": API_KEY, "units": "metric"}
        response = requests.get(base_url, params=params)
        response.raise_for_status() #HTTP error
        weather_data = response.json()
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError:
         print("JSONDecodeError: Could not decode the JSON response.")
         return None
    except HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def show_weather(weather_data):
    if weather_data:
        print(f"Weather in {city_name}, {weather_data['location']['region']}:")
        print(f"Temperature: {weather_data['current']['temp_c']}°C")
        print(f"Condition: {weather_data['current']['condition']['text']}")
    else:
        print(f"Could not retrieve weather data for {city_name}")

if __name__ == "__main__":
   # main()
    city_name = get_city_name()
    current_weather = get_weather(city_name)
    show_weather(current_weather)
    