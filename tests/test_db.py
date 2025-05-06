import os

import pytest
from sqlmodel import select

from weather_app.database import Database
from weather_app.models import Location, UserSettings, WeatherRecord


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
def session(test_db):
    """Create a new database session for a test"""
    with test_db.session() as session:
        yield session


def test_database_initialization(test_db):
    """Test that the database initializes correctly"""
    # Should have an engine
    assert test_db._engine is not None
    # Should be a SQLite database for testing
    assert str(test_db._engine.url).startswith("sqlite")


def test_create_location(session):
    """Test creating and retrieving a location"""
    # Create a test location
    test_location = Location(
        name="London",
        latitude=51.5074,
        longitude=-0.1278,
        country="United Kingdom",
        region="Greater London",
    )
    session.add(test_location)
    session.commit()
    session.refresh(test_location)

    # Query the location back
    statement = select(Location).where(Location.name == "London")
    results = session.exec(statement)
    db_location = results.first()

    assert db_location is not None
    assert db_location.name == "London"
    assert db_location.country == "United Kingdom"
    assert db_location.latitude == 51.5074
    assert db_location.longitude == -0.1278


def test_create_weather_record(session):
    """Test creating and retrieving a weather record with relationship"""
    # Create a test location
    test_location = Location(
        name="Paris", latitude=48.8566, longitude=2.3522, country="France"
    )
    session.add(test_location)
    session.commit()
    session.refresh(test_location)

    # Create a weather record for this location
    test_record = WeatherRecord(
        location_id=test_location.id,
        temperature=22.5,
        feels_like=23.0,
        humidity=65,
        condition="Sunny",
    )
    session.add(test_record)
    session.commit()
    session.refresh(test_record)

    # Query the record back with relationship
    statement = select(WeatherRecord).where(
        WeatherRecord.location_id == test_location.id
    )
    results = session.exec(statement)
    db_record = results.first()

    assert db_record is not None
    assert db_record.temperature == 22.5
    assert db_record.condition == "Sunny"
    assert db_record.location_id == test_location.id


def test_user_settings(session):
    """Test creating and retrieving user settings"""
    # Create user settings
    settings = UserSettings(
        temperature_unit="fahrenheit", wind_speed_unit="mph", theme="dark"
    )
    session.add(settings)
    session.commit()
    session.refresh(settings)

    # Query the settings back
    statement = select(UserSettings)
    results = session.exec(statement)
    db_settings = results.first()

    assert db_settings is not None
    assert db_settings.temperature_unit == "fahrenheit"
    assert db_settings.wind_speed_unit == "mph"
    assert db_settings.theme == "dark"
