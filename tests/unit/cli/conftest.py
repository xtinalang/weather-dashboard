"""
Configuration file for pytest.

This file contains shared fixtures and configurations that can be used by
all test files.
"""

import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from weather_app.api import WeatherAPI
from weather_app.display import WeatherDisplay
from weather_app.models import Location, UserSettings, WeatherRecord
from weather_app.repository import (
    LocationRepository,
    SettingsRepository,
    WeatherRepository,
)

# Add the project root to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",  # In-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a new database session for testing."""
    with Session(test_db_engine) as session:
        yield session


@pytest.fixture
def mock_database(test_db_engine):
    """Create a properly mocked Database instance."""

    # Create a real Database-like object instead of mocking the class
    class MockDatabase:
        def __init__(self):
            self._engine = test_db_engine

        def get_engine(self):
            return self._engine

        @contextmanager
        def get_session(self):
            with Session(self._engine) as session:
                yield session

        @classmethod
        def create_tables(cls):
            pass

        @classmethod
        def get_database_path(cls):
            return "sqlite:///:memory:"

    return MockDatabase()


@pytest.fixture
def mock_location_repo(test_db_session, test_db_engine):
    """Create a LocationRepository with a mocked database.

    Uses the test session.
    """
    # Create a mock database that uses the test session
    mock_db = MagicMock()
    mock_db.get_session.return_value.__enter__.return_value = test_db_session
    mock_db.get_session.return_value.__exit__.return_value = None

    with patch("weather_app.repository.Database") as MockDatabaseClass:
        with patch("weather_app.repository.Database.get_engine") as get_engine:
            MockDatabaseClass.return_value = mock_db
            get_engine.return_value = test_db_engine

            repo = LocationRepository()
            repo.db = mock_db
            return repo


@pytest.fixture
def mock_settings_repo(test_db_session, test_db_engine):
    """Create a SettingsRepository with a mocked database.

    Uses the test session.
    """
    # Create a mock database that uses the test session
    mock_db = MagicMock()
    mock_db.get_session.return_value.__enter__.return_value = test_db_session
    mock_db.get_session.return_value.__exit__.return_value = None

    with patch("weather_app.repository.Database") as MockDatabaseClass:
        with patch("weather_app.repository.Database.get_engine") as get_engine:
            MockDatabaseClass.return_value = mock_db
            get_engine.return_value = test_db_engine

            repo = SettingsRepository()
            repo.db = mock_db
            return repo


@pytest.fixture
def mock_weather_repo(test_db_session, test_db_engine):
    """Create a WeatherRepository with a mocked database.

    Uses the test session.
    """
    # Create a mock database that uses the test session
    mock_db = MagicMock()
    mock_db.get_session.return_value.__enter__.return_value = test_db_session
    mock_db.get_session.return_value.__exit__.return_value = None

    with patch("weather_app.repository.Database") as MockDatabaseClass:
        with patch("weather_app.repository.Database.get_engine") as get_engine:
            MockDatabaseClass.return_value = mock_db
            get_engine.return_value = test_db_engine

            repo = WeatherRepository()
            repo.db = mock_db
            return repo


@pytest.fixture
def mock_api():
    """Create a mocked WeatherAPI instance."""
    api = MagicMock(spec=WeatherAPI)

    # Mock get_weather method
    api.get_weather.return_value = {
        "location": {
            "name": "London",
            "country": "UK",
            "lat": 51.52,
            "lon": -0.11,
            "localtime": "2023-05-07 12:00",
        },
        "current": {
            "temp_c": 18.0,
            "temp_f": 64.4,
            "condition": {
                "text": "Partly cloudy",
                "icon": ("//cdn.weatherapi.com/weather/64x64/" "day/116.png"),
            },
            "wind_kph": 14.4,
            "wind_mph": 8.9,
            "humidity": 68,
            "feelslike_c": 17.5,
            "feelslike_f": 63.5,
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2023-05-07",
                    "day": {
                        "maxtemp_c": 20.5,
                        "maxtemp_f": 68.9,
                        "mintemp_c": 11.2,
                        "mintemp_f": 52.2,
                        "condition": {
                            "text": "Partly cloudy",
                            "icon": (
                                "//cdn.weatherapi.com/weather/" "64x64/day/116.png"
                            ),
                        },
                    },
                },
                {
                    "date": "2023-05-08",
                    "day": {
                        "maxtemp_c": 22.1,
                        "maxtemp_f": 71.8,
                        "mintemp_c": 12.5,
                        "mintemp_f": 54.5,
                        "condition": {
                            "text": "Sunny",
                            "icon": (
                                "//cdn.weatherapi.com/weather/" "64x64/day/113.png"
                            ),
                        },
                    },
                },
            ]
        },
    }

    # Mock search_city method
    api.search_city.return_value = [
        {
            "id": 1,
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "url": "london-city-of-london-greater-london-united-kingdom",
        }
    ]

    return api


@pytest.fixture
def mock_display():
    """Create a mocked WeatherDisplay instance."""
    return MagicMock(spec=WeatherDisplay)


@pytest.fixture
def sample_location():
    """Create a sample Location instance for testing."""
    return Location(
        id=1,
        name="London",
        latitude=51.52,
        longitude=-0.11,
        country="United Kingdom",
        region="Greater London",
        is_favorite=False,
    )


@pytest.fixture
def sample_user_settings():
    """Create a sample UserSettings instance for testing."""
    return UserSettings(
        id=1,
        temperature_unit="celsius",
        wind_speed_unit="m/s",
        save_history=True,
        max_history_days=7,
        theme="default",
        forecast_days=7,
    )


@pytest.fixture
def sample_weather_record(sample_location):
    """Create a sample WeatherRecord instance for testing."""
    return WeatherRecord(
        id=1,
        location_id=sample_location.id,
        timestamp=datetime(2023, 5, 7, 12, 0, 0),
        temperature=18.0,
        feels_like=17.5,
        humidity=68,
        pressure=1015.0,
        wind_speed=14.4,
        wind_direction="WSW",
        condition="Partly cloudy",
        condition_description="Partly cloudy throughout the day",
    )


# You can define shared fixtures here that will be available to all test files
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup any environment variables needed for testing."""
    # Set to test mode
    os.environ["TESTING"] = "True"

    # Use SQLite for testing
    if "WEATHER_APP_DATABASE_URL" not in os.environ:
        os.environ["WEATHER_APP_DATABASE_URL"] = "sqlite:///:memory:"

    yield

    # Clean up
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
