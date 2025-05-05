# Weather Dashboard

A weather dashboard application with PostgreSQL database integration for storing weather data, locations, and user preferences.

## Project Structure

```
weather_app/
├── __init__.py       # Sets up basic logging config
├── __main__.py       # `python -m weather_app` entry point (runs app)
├── app.py            # Main WeatherApp class (application orchestration)
├── api.py            # WeatherAPI class (HTTP communication)
├── cli.py            # Typer-based CLI (user prompts, commands)
├── display.py        # WeatherDisplay class (terminal output)
├── display_types.py  # Type definitions for display data
├── location.py       # LocationManager (search and select locations)
├── exceptions.py     # Custom exceptions
├── models.py         # SQLModel models for database entities
├── database.py       # Database connection manager
├── repository.py     # CRUD operations for database entities
```

## Features

- Current weather conditions and forecasts
- Location search and favorites
- Historical weather data storage
- User preferences (temperature unit, etc.)
- PostgreSQL database integration with SQLModel ORM
- Data persistence across application restarts

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL (or SQLite for local development)
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

4. Update the .env file with your API key and database settings.

### PostgreSQL Setup

For detailed PostgreSQL setup instructions, see [POSTGRES_SETUP.md](POSTGRES_SETUP.md).

### Running the App

```bash
python -m weather_app
```

## Tests

```
tests/
├── __init__.py
├── test_api.py
├── test_cli.py
├── test_location.py
├── test_display.py
├── test_app.py
```

Run tests with:
```bash
pytest
```

## Database Schema

The application uses SQLModel with the following entities:

- **Location**: Stores location data (name, coordinates, etc.)
- **WeatherRecord**: Stores weather data for locations
- **UserSettings**: Stores user preferences

The schema supports both SQLite (for development) and PostgreSQL (for production).
