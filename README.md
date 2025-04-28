# weather-dashboard

```
weather_app/
├── config.py # This may become a config folder
├── logger.py
├── app.py
├── api/
│   └── weather_api.py
├── ui/
│   ├── user_input.py
│   ├── weather_formatter.py   # Potential New file
│   └── weather_display.py     
├── handlers/
│   └── location_manager.py
├── models/
```
#### Other option

```
weather_app/
├── __main__.py                # Entry point (currently your if __name__ == "__main__")
├── config.py                  # Configuration and constants (e.g. default location, units)
├── api/
│   └── weather_api.py         # WeatherAPI class
├── cli/
│   ├── user_input.py          # User_Input_Information class
│   ├── display.py             # WeatherDisplay class
│   └── location_manager.py    # LocationManager class
├── core/
│   └── app.py 
├── models/
│              
├── logs/
│   └── weather_app.log        # Output log (you already handle this)
└── requirements.txt     
```