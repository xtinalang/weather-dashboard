"""Shared fixtures for integration tests."""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

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
