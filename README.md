# Weather Dashboard

A weather dashboard application with SQLite database integration for storing weather data, locations, and user preferences.

## Project Structure

```
weather_app/
├── __init__.py       # Sets up basic logging config
├── __main__.py       # `python -m weather_app` entry point (runs app)
├── app.py            # Main WeatherApp class (application orchestration)
├── api.py            # WeatherAPI class (HTTP communication)
├── cli.py            # Typer-based CLI (user prompts, commands)
├── display.py        # WeatherDisplay class (terminal output)
├── current.py        # CurrentWeatherManager for fetching current weather
├── forecast.py       # ForecastManager for fetching forecast data
├── display_types.py  # Type definitions for display data
├── location.py       # LocationManager (search and select locations)
├── exceptions.py     # Custom exceptions
├── models.py         # SQLModel models for database entities
├── database.py       # Database connection manager with SQLite
├── repository.py     # CRUD operations for database entities
```

## Features

- Current weather conditions and forecasts
- Location search and favorites
- Historical weather data storage
- User preferences (temperature unit, etc.)
- SQLite database integration with SQLModel ORM
- Data persistence across application restarts

## Setup

### Prerequisites

- Python 3.9+
- Weather API key (from weatherapi.com)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/weather-dashboard.git
   cd weather-dashboard
   ```

2. Install dependencies:
   ```bash
   pip install .
   ```

3. Create an environment file:
   ```bash
   cp .env-template .env
   ```

4. Update the .env file with your API key.

### Database Setup

The application uses SQLite by default and will create a database file at `~/.weather_app/weather.db`. You can initialize the database and add sample data by running:

```bash
python init_database.py
```

### Running the App

```bash
python -m weather_app interactive
```

You can also use other CLI commands:

```bash
# Get current weather
python -m weather_app current

# Get a forecast
python -m weather_app forecast

# Initialize database
python -m weather_app init-db

# Run diagnostics
python -m weather_app diagnostics
```

## Tests

You can test the application's core functionality with:

```bash
python test_location.py
```

## Database Schema

The application uses SQLModel with the following entities:

- **Location**: Stores location data (name, coordinates, etc.)
- **WeatherRecord**: Stores weather data for locations
- **UserSettings**: Stores user preferences

## Troubleshooting

If you encounter session-related errors or "Error retrieving location" messages, try these steps:

1. Initialize the database: `python init_database.py`
2. Run the diagnostics: `python -m weather_app diagnostics`
3. Test location handling: `python test_location.py`
