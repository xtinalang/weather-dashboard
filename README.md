# weather-dashboard

##APP

```
weather_app/
├── __init__.py       # Sets up basic logging config
├── __main__.py       # `python -m weather_app` entry point (runs app)
├── app.py            # Main WeatherApp class (application orchestration)
├── api.py            # WeatherAPI class (HTTP communication)
├── cli.py            # Typer-based CLI (user prompts, commands)
├── display.py        # WeatherDisplay class (terminal output)
├── location.py       # LocationManager (search and select locations)
├── exceptions.py     # Custom exceptions (APIError, InputError, etc.)
├── models.py         # Your data classes (e.g. dataclass, NamedTuple, Pydantic, but more likely sqlmodel models when we add DB persistence ...)

```
##Tests

```
tests/
├── __init__.py
├── test_api.py
├── test_cli.py
├── test_location.py
├── test_display.py
├── test_app.py
```
