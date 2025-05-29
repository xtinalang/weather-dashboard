"""Shared fixtures for integration tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import inspect, text
from typer.testing import CliRunner

from weather_app.database import Database


@pytest.fixture(scope="session")
def integration_test_db():
    """Create a session-scoped test database for integration tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    # Store original DATABASE_URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set test database URL
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    # Initialize database
    db = Database()
    db.create_tables()

    yield test_db_path

    # Cleanup
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        os.environ.pop("DATABASE_URL", None)

    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture
def clean_db(integration_test_db):
    """Provide a clean database for each test."""
    # Clear all tables before each test
    db = Database()
    with db.get_session() as session:
        # Get all table names
        inspector = inspect(Database.get_engine())
        table_names = inspector.get_table_names()

        # Clear all tables (in reverse order to handle foreign keys)
        for table_name in reversed(table_names):
            session.execute(text(f"DELETE FROM {table_name}"))
        session.commit()

    yield integration_test_db


@pytest.fixture
def cli_runner():
    """Create a CLI runner for integration testing."""
    return CliRunner()


@pytest.fixture
def mock_weather_data():
    """Mock weather API response data shared across all tests."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "tz_id": "Europe/London",
            "localtime": "2024-01-15 14:30",
        },
        "current": {
            "temp_c": 15.0,
            "temp_f": 59.0,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            },
            "wind_mph": 6.9,
            "wind_kph": 11.2,
            "wind_dir": "W",
            "pressure_mb": 1020.0,
            "humidity": 72,
            "feelslike_c": 15.0,
            "feelslike_f": 59.0,
            "vis_km": 10.0,
            "uv": 3.0,
            "precip_mm": 0.0,
            "last_updated": "2024-01-15 14:30",
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2024-01-15",
                    "day": {
                        "maxtemp_c": 18.0,
                        "maxtemp_f": 64.4,
                        "mintemp_c": 12.0,
                        "mintemp_f": 53.6,
                        "condition": {
                            "text": "Partly cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                        },
                        "maxwind_mph": 8.7,
                        "maxwind_kph": 14.0,
                        "daily_chance_of_rain": 20,
                        "daily_chance_of_snow": 0,
                        "totalprecip_mm": 0.1,
                        "totalprecip_in": 0.0,
                        "avghumidity": 75,
                        "uv": 3.0,
                    },
                },
                {
                    "date": "2024-01-16",
                    "day": {
                        "maxtemp_c": 16.0,
                        "maxtemp_f": 60.8,
                        "mintemp_c": 10.0,
                        "mintemp_f": 50.0,
                        "condition": {
                            "text": "Cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/119.png",
                        },
                        "maxwind_mph": 10.0,
                        "maxwind_kph": 16.1,
                        "daily_chance_of_rain": 30,
                        "daily_chance_of_snow": 0,
                        "totalprecip_mm": 0.2,
                        "totalprecip_in": 0.01,
                        "avghumidity": 80,
                        "uv": 2.0,
                    },
                },
            ]
        },
    }


@pytest.fixture
def mock_weather_api(mock_weather_data):
    """Create a configured mock weather API."""
    mock_api = MagicMock()
    mock_api.get_weather.return_value = mock_weather_data
    mock_api.get_forecast.return_value = mock_weather_data
    mock_api.search_city.return_value = [
        {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
        }
    ]
    return mock_api


def assert_cli_success(result, expected_message=None):
    """Helper function to assert CLI command success."""
    assert result.exit_code == 0
    if expected_message:
        assert expected_message in result.stdout


def assert_web_response(response, expected_status=200, content_check=None):
    """Helper function to assert web response."""
    if isinstance(expected_status, list):
        assert response.status_code in expected_status
    else:
        assert response.status_code == expected_status

    if content_check:
        assert content_check in response.data
