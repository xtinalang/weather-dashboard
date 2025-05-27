import os
from datetime import datetime, timedelta

import pytest

from weather_app.database import Database
from weather_app.models import Location, UserSettings, WeatherRecord
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
        if "WEATHER_APP_DATABASE_URL" in os.environ:
            del os.environ["WEATHER_APP_DATABASE_URL"]

    # Reset the Database singleton
    Database._instance = None
    Database._engine = None


@pytest.fixture
def location_repo(test_db):
    """Create a fresh LocationRepository for each test"""
    return LocationRepository()


@pytest.fixture
def weather_repo(test_db):
    """Create a fresh WeatherRepository for each test"""
    return WeatherRepository()


@pytest.fixture
def settings_repo(test_db):
    """Create a fresh SettingsRepository for each test"""
    return SettingsRepository()


@pytest.fixture
def sample_location(location_repo):
    """Create a sample location for testing"""
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
    # Clear any existing data first (delete weather records first
    # due to foreign key constraints)
    with location_repo.db.get_session() as session:
        session.query(WeatherRecord).delete()
        session.query(Location).delete()
        session.commit()

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
    # Clear any existing data first (delete weather records first
    # due to foreign key constraints)
    with location_repo.db.get_session() as session:
        session.query(WeatherRecord).delete()
        session.query(Location).delete()
        session.commit()

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
    # Clear any existing settings first
    with settings_repo.db.get_session() as session:
        session.query(UserSettings).delete()
        session.commit()

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


def test_location_repo_create(mock_location_repo, test_db_session, sample_location):
    """Test creating a location."""
    # Create a location using the repository
    result = mock_location_repo.create(sample_location)

    # Check that the location was created successfully
    assert result.id is not None
    assert result.name == sample_location.name
    assert result.latitude == sample_location.latitude
    assert result.longitude == sample_location.longitude


def test_location_repo_get_by_id(mock_location_repo, test_db_session):
    """Test getting a location by ID."""
    # Create a location first
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)

    # Get the location by ID using the repository
    result = mock_location_repo.get_by_id(location.id)

    # Check that the location was retrieved
    assert result is not None
    assert result.id == location.id
    assert result.name == location.name


def test_location_repo_find_by_coordinates(mock_location_repo, test_db_session):
    """Test finding a location by coordinates."""
    # Create a location first
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)

    # Find the location by coordinates using the repository
    result = mock_location_repo.find_by_coordinates(
        location.latitude, location.longitude
    )

    # Check that the location was found
    assert result is not None
    assert result.id == location.id
    assert result.name == location.name


def test_location_repo_get_favorites(mock_location_repo, test_db_session):
    """Test getting favorite locations."""
    # Create favorite and non-favorite locations
    favorite = Location(
        name="Paris", latitude=48.85, longitude=2.35, country="France", is_favorite=True
    )
    not_favorite = Location(
        name="Berlin",
        latitude=52.52,
        longitude=13.40,
        country="Germany",
        is_favorite=False,
    )

    # Add locations to the database
    test_db_session.add(favorite)
    test_db_session.add(not_favorite)
    test_db_session.commit()

    # Get favorite locations
    favorites = mock_location_repo.get_favorites()

    # Check that only the favorite location was returned
    assert len(favorites) == 1
    assert favorites[0].name == favorite.name
    assert favorites[0].is_favorite is True


def test_location_repo_update(mock_location_repo, test_db_session):
    """Test updating a location."""
    # Create a location first
    location = Location(
        name="Original City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
        is_favorite=False,
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)

    # Update the location using the repository
    updated = mock_location_repo.update(
        location.id, {"name": "New London", "is_favorite": True}
    )

    # Check that the location was updated
    assert updated is not None
    assert updated.name == "New London"
    assert updated.is_favorite is True
    # Other fields should remain unchanged
    assert updated.latitude == location.latitude


def test_location_repo_delete(mock_location_repo, test_db_session):
    """Test deleting a location."""
    # Create a location first
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)
    location_id = location.id

    # Delete the location using the repository
    result = mock_location_repo.delete(location_id)

    # Check that the location was deleted
    assert result is True


def test_settings_repo_get_settings(mock_settings_repo, test_db_session):
    """Test getting application settings."""
    # Get settings (this should create defaults if none exist)
    settings = mock_settings_repo.get_settings()

    # Check that settings were created
    assert settings is not None
    assert settings.id == 1
    assert settings.temperature_unit == "celsius"

    # Verify in the database
    db_settings = test_db_session.get(UserSettings, 1)
    assert db_settings is not None


def test_settings_repo_update_temperature_unit(
    mock_settings_repo, test_db_session, sample_user_settings
):
    """Test updating temperature unit."""
    # Add settings to the database
    test_db_session.add(sample_user_settings)
    test_db_session.commit()

    # Update temperature unit
    updated = mock_settings_repo.update_temperature_unit("fahrenheit")

    # Check that the settings were updated
    assert updated.temperature_unit == "fahrenheit"

    # Verify in the database
    db_settings = test_db_session.get(UserSettings, 1)
    assert db_settings.temperature_unit == "fahrenheit"


def test_weather_repo_get_by_location(mock_weather_repo, test_db_session):
    """Test getting weather records for a location."""
    # Create a location first
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)

    # Create a weather record
    weather_record = WeatherRecord(
        location_id=location.id,
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
    test_db_session.add(weather_record)
    test_db_session.commit()
    test_db_session.refresh(weather_record)

    # Get weather records for the location using the repository
    records = mock_weather_repo.get_by_location(location.id)

    # Check that the weather record was returned
    assert len(records) == 1
    assert records[0].temperature == weather_record.temperature


def test_weather_repo_get_latest_for_location(mock_weather_repo, test_db_session):
    """Test getting the latest weather record for a location."""
    # Create a location first
    location = Location(
        name="Test City",
        latitude=40.7128,
        longitude=-74.0060,
        country="Test Country",
        region="Test Region",
    )
    test_db_session.add(location)
    test_db_session.commit()
    test_db_session.refresh(location)

    # Create a weather record
    weather_record = WeatherRecord(
        location_id=location.id,
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
    test_db_session.add(weather_record)
    test_db_session.commit()
    test_db_session.refresh(weather_record)

    # Get the latest weather record using the repository
    record = mock_weather_repo.get_latest_for_location(location.id)

    # Check that the weather record was returned
    assert record is not None
    assert record.temperature == weather_record.temperature
