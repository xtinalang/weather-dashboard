import os
from datetime import datetime, timedelta

import pytest

from weather_app.database import Database
from weather_app.models import Location, WeatherRecord
from weather_app.repository import (
    LocationRepository,
    SettingsRepository,
    WeatherRepository,
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database connection"""
    # Save the original DATABASE_URL
    original_url = os.environ.get("WEATHER_APP_DATABASE_URL")

    # Set a test in-memory SQLite database
    os.environ["WEATHER_APP_DATABASE_URL"] = "sqlite:///:memory:"

    # Reset the Database singleton for testing
    Database._instance = None
    Database._engine = None

    # Initialize the database
    db = Database()
    db.create_tables()

    yield db

    # Clean up
    if original_url:
        os.environ["WEATHER_APP_DATABASE_URL"] = original_url
    else:
        del os.environ["WEATHER_APP_DATABASE_URL"]

    # Reset the Database singleton
    Database._instance = None
    Database._engine = None


@pytest.fixture
def location_repo(test_db):
    return LocationRepository()


@pytest.fixture
def weather_repo(test_db):
    return WeatherRepository()


@pytest.fixture
def settings_repo(test_db):
    return SettingsRepository()


@pytest.fixture
def sample_location(location_repo):
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
        is_favorite=True,
    )
    return location_repo.create(location)


def test_location_create_and_get(location_repo):
    """Test creating and getting a location"""
    # Create a location
    location = Location(
        name="New York",
        latitude=40.7128,
        longitude=-74.0060,
        country="USA",
        region="NY",
    )
    saved_location = location_repo.create(location)

    # Get by ID
    retrieved_location = location_repo.get_by_id(saved_location.id)

    assert retrieved_location is not None
    assert retrieved_location.name == "New York"
    assert retrieved_location.country == "USA"
    assert retrieved_location.id == saved_location.id


def test_location_search(location_repo):
    """Test searching for locations"""
    # Create multiple locations
    locations = [
        Location(name="New York", latitude=40.7128, longitude=-74.0060, country="USA"),
        Location(
            name="Los Angeles", latitude=34.0522, longitude=-118.2437, country="USA"
        ),
        Location(name="London", latitude=51.5074, longitude=-0.1278, country="UK"),
    ]

    for loc in locations:
        location_repo.create(loc)

    # Search by name
    results = location_repo.search("New")
    assert len(results) == 1
    assert results[0].name == "New York"

    # Search by country
    results = location_repo.search("USA")
    assert len(results) == 2
    assert {loc.name for loc in results} == {"New York", "Los Angeles"}


def test_location_favorites(location_repo):
    """Test getting favorite locations"""
    # Create multiple locations with different favorite status
    locations = [
        Location(
            name="New York",
            latitude=40.7128,
            longitude=-74.0060,
            country="USA",
            is_favorite=True,
        ),
        Location(
            name="Los Angeles",
            latitude=34.0522,
            longitude=-118.2437,
            country="USA",
            is_favorite=False,
        ),
        Location(
            name="London",
            latitude=51.5074,
            longitude=-0.1278,
            country="UK",
            is_favorite=True,
        ),
    ]

    for loc in locations:
        location_repo.create(loc)

    # Get favorites
    favorites = location_repo.get_favorites()
    assert len(favorites) == 2
    assert {loc.name for loc in favorites} == {"New York", "London"}


def test_weather_create_and_get(weather_repo, sample_location):
    """Test creating and getting weather records"""
    # Create a weather record
    weather = WeatherRecord(
        location_id=sample_location.id,
        temperature=25.5,
        feels_like=26.0,
        humidity=70,
        pressure=1015.0,
        wind_speed=10.5,
        wind_direction="NE",
        condition="Sunny",
        condition_description="Clear sky",
    )
    saved_weather = weather_repo.create(weather)

    # Get by ID
    retrieved_weather = weather_repo.get_by_id(saved_weather.id)

    assert retrieved_weather is not None
    assert retrieved_weather.temperature == 25.5
    assert retrieved_weather.condition == "Sunny"
    assert retrieved_weather.location_id == sample_location.id


def test_weather_by_location(weather_repo, sample_location):
    """Test getting weather records for a location"""
    # Create multiple weather records for the same location
    weather_records = [
        WeatherRecord(
            location_id=sample_location.id,
            temperature=25.5,
            condition="Sunny",
            timestamp=datetime.now() - timedelta(hours=3),
        ),
        WeatherRecord(
            location_id=sample_location.id,
            temperature=20.0,
            condition="Cloudy",
            timestamp=datetime.now() - timedelta(hours=6),
        ),
        WeatherRecord(
            location_id=sample_location.id,
            temperature=18.5,
            condition="Rainy",
            timestamp=datetime.now() - timedelta(hours=9),
        ),
    ]

    for record in weather_records:
        weather_repo.create(record)

    # Get records for location
    location_records = weather_repo.get_by_location(sample_location.id)
    assert len(location_records) == 3

    # Check if they are ordered by timestamp (descending)
    assert location_records[0].temperature == 25.5  # Most recent first
    assert location_records[1].temperature == 20.0
    assert location_records[2].temperature == 18.5


def test_settings_repository(settings_repo):
    """Test user settings operations"""
    # Get default settings (should be created if none exist)
    settings = settings_repo.get_settings()
    assert settings is not None
    assert settings.temperature_unit == "celsius"  # Default value

    # Update temperature unit
    updated_settings = settings_repo.update_temperature_unit("fahrenheit")
    assert updated_settings.temperature_unit == "fahrenheit"

    # Get settings again to verify persistence
    settings = settings_repo.get_settings()
    assert settings.temperature_unit == "fahrenheit"
