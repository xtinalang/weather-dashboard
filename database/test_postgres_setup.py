import os

import psycopg2
import pytest
from decouple import config
from sqlalchemy import create_engine, text

from weather_app.database import get_database_url


def test_postgres_env_variables():
    """Test if PostgreSQL environment variables are set"""
    # Check for required environment variables
    required_vars = {
        "POSTGRES_USER": config("DB_USER"),
        "POSTGRES_PASSWORD": config("DB_PASSWORD"),
        "POSTGRES_HOST": config("DB_HOST", "localhost"),
        "POSTGRES_PORT": config("DB_PORT", "5432"),
        "POSTGRES_DB": config("DB_NAME", "weather_db"),
    }

    # Print current environment variables (without password)
    print("\nCurrent PostgreSQL environment variables:")
    for key, value in required_vars.items():
        if key != "POSTGRES_PASSWORD":
            print(f"{key}: {value}")

    # Check if .env file exists
    env_file = os.path.join(os.getcwd(), ".env")
    assert os.path.exists(env_file), f".env file not found at {env_file}"

    # Try to load variables from .env
    try:
        db_url = config("DATABASE_URL", default=None)
        assert db_url is not None, "DATABASE_URL not found in .env file"
        print(f"\nDatabase URL from .env: {db_url}")
    except Exception as e:
        pytest.fail(f"Failed to load .env file: {str(e)}")


def test_postgres_connection():
    """Test PostgreSQL connection using environment variables"""
    try:
        # Get connection details from environment
        user = config("DB_USER")
        password = config("DB_PASSWORD")
        host = config("DB_HOST", "localhost")
        port = config("DB_PORT", "5432")
        dbname = config("DB_NAME", "weather_db")

        # Try to connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )

        # Test connection
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"\nPostgreSQL version: {version[0]}")

        conn.close()
        assert True, "Successfully connected to PostgreSQL"

    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL: {str(e)}")


def test_create_postgres_database():
    """Test creating a new PostgreSQL database"""
    try:
        # Get connection details from environment
        user = config("DB_USER")
        password = config("DB_PASSWORD")
        host = config("DB_HOST", "localhost")
        port = config("DB_PORT", "5432")
        dbname = config("DB_NAME", "weather_db")

        # Connect to default postgres database
        conn = psycopg2.connect(
            dbname="postgres", user=user, password=password, host=host, port=port
        )
        conn.autocommit = True

        # Create new database if it doesn't exist
        with conn.cursor() as cur:
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cur.fetchone()

            if not exists:
                print(f"\nCreating database: {dbname}")
                cur.execute(f"CREATE DATABASE {dbname}")
                print(f"Database {dbname} created successfully")
            else:
                print(f"\nDatabase {dbname} already exists")

        conn.close()

        # Verify we can connect to the new database
        test_conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        test_conn.close()

        assert True, "Successfully created and verified PostgreSQL database"

    except Exception as e:
        pytest.fail(f"Failed to create PostgreSQL database: {str(e)}")


def test_postgres_user_permissions():
    """Test PostgreSQL user permissions"""
    try:
        # Get connection details from environment
        user = config("DB_USER")
        password = config("DB_PASSWORD")
        host = config("DB_HOST", "localhost")
        port = config("DB_PORT", "5432")
        dbname = config("DB_NAME", "weather_db")

        # Connect to the database
        conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )

        # Test user permissions
        with conn.cursor() as cur:
            # Test CREATE TABLE permission
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_permissions (
                    id SERIAL PRIMARY KEY,
                    test_column TEXT
                )
            """)

            # Test INSERT permission
            cur.execute("""
                INSERT INTO test_permissions (test_column)
                VALUES ('test')
            """)

            # Test SELECT permission
            cur.execute("SELECT * FROM test_permissions")
            assert cur.fetchone() is not None, "Could not read test data"

            # Test UPDATE permission
            cur.execute("""
                UPDATE test_permissions
                SET test_column = 'updated'
                WHERE test_column = 'test'
            """)

            # Test DELETE permission
            cur.execute("DELETE FROM test_permissions")

            # Clean up
            cur.execute("DROP TABLE test_permissions")

        conn.commit()
        conn.close()

        assert True, "Successfully tested PostgreSQL user permissions"

    except Exception as e:
        pytest.fail(f"Failed to test PostgreSQL user permissions: {str(e)}")


def test_sqlalchemy_connection():
    """Test SQLAlchemy connection using environment variables"""
    try:
        # Get database URL from environment
        db_url = get_database_url()

        # Create engine
        engine = create_engine(db_url)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"\nSQLAlchemy connected to PostgreSQL version: {version}")

        assert True, "Successfully connected using SQLAlchemy"

    except Exception as e:
        pytest.fail(f"Failed to connect using SQLAlchemy: {str(e)}")
