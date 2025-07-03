"""Tests for the Database module."""

import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from weather_app.database import Database, get_session, init_db
from weather_app.models import Location


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """
    Provide database URL via environment variables.

    Yields:
        None
    """
    db_url = "sqlite:///:memory:"
    with patch.dict(os.environ, {"WEATHER_APP_DATABASE_URL": db_url}):
        yield


@pytest.fixture
def mock_db() -> MagicMock:
    """
    Create a mock database instance.

    Returns:
        MagicMock: Mock database object
    """
    mock_db = MagicMock()
    mock_db.get_engine.return_value = MagicMock()
    return mock_db


@patch("weather_app.database.DATABASE_URL", "sqlite:///test.db")
@patch("weather_app.database.create_engine")
def test_database_initialize(mock_create_engine: MagicMock) -> None:
    """Test database initialization with SQLite."""
    # Reset the singleton instance
    Database._instance = None
    Database._engine = None

    # Create database instance which should trigger initialization
    Database()

    # Check that create_engine was called
    mock_create_engine.assert_called_once()
    # Assert it's using SQLite
    call_args = mock_create_engine.call_args
    assert "sqlite:///" in call_args[0][0]


@patch("weather_app.database.DATABASE_URL", "sqlite:///test.db")
@patch("weather_app.database.create_engine")
def test_database_singleton(mock_create_engine: MagicMock) -> None:
    """Test the singleton pattern of the Database class."""
    # Reset the singleton instance
    Database._instance = None
    Database._engine = None

    # Create two database instances
    db1 = Database()
    db2 = Database()

    # Check that they are the same instance
    assert db1 is db2

    # Check that create_engine was called exactly once
    assert mock_create_engine.call_count == 1


@patch("sqlmodel.SQLModel.metadata.create_all")
def test_create_tables(mock_create_all: MagicMock) -> None:
    """Test that tables are created properly."""
    # Reset the singleton instance
    Database._instance = None
    Database._engine = None

    # Create a database instance and create tables
    with patch("weather_app.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database()
        db.create_tables()

        # Check that create_all was called with the engine
        mock_create_all.assert_called_once_with(mock_engine)


@patch("weather_app.database.Session")
def test_get_session(mock_session_class: MagicMock) -> None:
    """Test getting a database session."""
    # Setup mock session instance
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=None)

    # Reset the singleton instance
    Database._instance = None
    Database._engine = None

    # Create a database instance
    with patch("weather_app.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database()

        # Use the context manager
        with db.get_session() as session:
            # Test session operations
            session.query(Location)

        # Check that session was created with the engine
        mock_session_class.assert_called_with(mock_engine)


@patch("weather_app.database.Session")
def test_get_session_exception(mock_session_class: MagicMock) -> None:
    """Test session handling when an exception occurs."""
    # Setup mock session that raises an exception
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=None)

    # Reset the singleton instance
    Database._instance = None
    Database._engine = None

    # Create a database instance
    with patch("weather_app.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database()

        # Simulate an exception in the context manager
        try:
            with db.get_session():
                raise Exception("Test exception")
        except Exception:
            pass

        # The session context manager should handle cleanup automatically
        mock_session_class.assert_called_with(mock_engine)


@patch("weather_app.database.Database")
def test_init_db(mock_database_class: MagicMock) -> None:
    """Test initializing the database."""
    # Setup mock
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    # Call the function
    result = init_db()

    # Check that create_tables was called
    mock_db.create_tables.assert_called_once()
    # Check the return value
    assert result is mock_db


@patch("weather_app.database.Session")
@patch("weather_app.database.Database.get_engine")
def test_get_session_fastapi(
    mock_get_engine: MagicMock, mock_session_class: MagicMock
) -> None:
    """Test the FastAPI session generator."""
    # Setup mock engine and session
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=None)

    # Get a session
    session_gen = get_session()
    session = next(session_gen)

    # Check that it's the mock session
    assert session is mock_session

    # Finish the generator
    try:
        next(session_gen)
    except StopIteration:
        pass

    # Check that session was created with the engine
    mock_session_class.assert_called_with(mock_engine)
