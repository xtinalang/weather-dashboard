import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, TypeVar

from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)

# Default to a SQLite database in the user's home directory for local development
DEFAULT_SQLITE_PATH = Path.home() / ".weather_app" / "weather.db"

# Default PostgreSQL connection string if environment variable is not set
DEFAULT_PG_URL = "postgresql://postgres:postgres@localhost:5432/weather_app"

# Get database URL from environment or use default
DATABASE_URL = os.environ.get("WEATHER_APP_DATABASE_URL", DEFAULT_PG_URL)


class Database:
    """Database connection manager for the weather application"""

    _instance: Optional["Database"] = None
    _engine: Optional[Engine] = None

    def __new__(cls) -> "Database":
        """Singleton pattern to ensure only one database instance exists"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._initialize_db()
        return cls._instance

    @classmethod
    def _initialize_db(cls) -> None:
        """Initialize the database engine with the appropriate connection settings"""
        if DATABASE_URL.startswith("sqlite"):
            # Ensure directory exists for SQLite database
            db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect with SQLite optimizations
            connect_args = {"check_same_thread": False}
            cls._engine = create_engine(
                DATABASE_URL, connect_args=connect_args, echo=False
            )
        else:
            # For PostgreSQL
            # Configure connection pooling for PostgreSQL
            cls._engine = create_engine(
                DATABASE_URL,
                echo=False,  # Set to True for SQL logging
                pool_size=5,  # Number of connections to keep open
                max_overflow=10,  # Max extra connections when pool is full
                pool_timeout=30,  # Seconds to wait before timing out
                pool_recycle=1800,  # Recycle connections after 30 minutes
                pool_pre_ping=True,  # Verify connections before using
                poolclass=QueuePool,  # Use QueuePool for connection pooling
            )

        logger.info(f"Database initialized at {DATABASE_URL}")

    @classmethod
    def create_tables(cls) -> None:
        """Create all tables defined in SQLModel models"""
        # Import all models to ensure they're registered with SQLModel
        from .models import Location, UserSettings, WeatherRecord  # noqa: F401

        SQLModel.metadata.create_all(cls.get_engine())
        logger.info("Database tables created")

    @classmethod
    def get_engine(cls) -> Engine:
        """Get the SQLAlchemy engine instance"""
        if cls._engine is None:
            cls._initialize_db()
        assert cls._engine is not None, "Database engine not initialized"
        return cls._engine

    @classmethod
    @contextmanager
    def session(cls) -> Generator[Session, None, None]:
        """Context manager for database sessions"""
        session = Session(cls.get_engine())
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def init_db() -> "Database":
    """Initialize the database and create tables"""
    db = Database()
    db.create_tables()
    return db


def get_session() -> Generator[Session, None, None]:
    """Session dependency for FastAPI"""
    with Session(Database.get_engine()) as session:
        yield session
