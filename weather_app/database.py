import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, TypeVar

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)

# Default SQLite database path in the user's home directory
DEFAULT_SQLITE_PATH = Path.home() / ".weather_app" / "weather.db"

# Database URL will always be SQLite
DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"


class Database:
    """
    Database connection manager for the weather application.

    This class implements the singleton pattern to ensure only one database
    connection is active throughout the application lifetime.
    """

    _instance: Optional["Database"] = None
    _engine: Optional[Engine] = None

    def __new__(cls) -> "Database":
        """Singleton pattern to ensure only one database instance exists."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._initialize_db()
        return cls._instance

    @classmethod
    def _initialize_db(cls) -> None:
        """
        Initialize the database engine with SQLite connection settings.

        Creates the parent directory for the database file if it doesn't exist.
        """
        # Ensure directory exists for SQLite database
        db_path: Path = Path(DATABASE_URL.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect with SQLite optimizations
        connect_args: dict[str, bool] = {"check_same_thread": False}
        cls._engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
        logger.info(f"SQLite database initialized at {db_path}")

    @classmethod
    def create_tables(cls) -> None:
        """
        Create all tables defined in SQLModel models.

        Raises:
            Exception: If table creation fails
        """
        try:
            # Import all models to ensure they're registered with SQLModel
            from .models import Location, UserSettings, WeatherRecord  # noqa: F401

            SQLModel.metadata.create_all(cls.get_engine())
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    @classmethod
    def get_engine(cls) -> Engine:
        """
        Get the SQLAlchemy engine instance.

        Returns:
            Engine: SQLAlchemy engine for database connections

        Raises:
            AssertionError: If the engine is not initialized
        """
        if cls._engine is None:
            cls._initialize_db()
        assert cls._engine is not None, "Database engine not initialized"
        return cls._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session within a context manager.

        Yields:
            Session: An active SQLAlchemy session

        Raises:
            Exception: Re-raises any exceptions after rolling back the session
        """
        session: Session = Session(self.get_engine())
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def get_database_path(cls) -> str:
        """
        Get the path to the SQLite database file.

        Returns:
            str: Path to the database file
        """
        return str(DEFAULT_SQLITE_PATH)


def init_db() -> "Database":
    """
    Initialize the database and create tables.

    Returns:
        Database: Initialized database instance

    Raises:
        Exception: Re-raises any exceptions from database initialization
    """
    try:
        db: Database = Database()
        db.create_tables()
        logger.info("Database initialized successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """
    Session dependency for FastAPI.

    Yields:
        Session: An active database session
    """
    with Session(Database.get_engine()) as session:
        yield session
