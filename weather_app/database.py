import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, TypeVar

from decouple import config
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)

DATABASE_URL = config("DATABASE_URL")


class Database:
    """Database connection manager for the weather application."""

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
        """Initialize the database engine with appropriate settings."""
        # create another @classmethod to create the database from scratch
        if cls._engine is not None:
            return

        try:
            # SQLite-specific setup
            if DATABASE_URL.startswith("sqlite:///"):
                db_path: Path = Path(DATABASE_URL.replace("sqlite:///", ""))
                db_path.parent.mkdir(parents=True, exist_ok=True)
                connect_args = {"check_same_thread": False}
            else:
                connect_args = {}

            # Create the engine
            cls._engine = create_engine(
                DATABASE_URL,
                connect_args=connect_args,
                echo=False,
                pool_pre_ping=True,  # Enable connection health checks
            )

            # Test the connection
            with cls._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            cls._engine = None  # Reset engine on failure
            raise

    @classmethod
    def create_tables(cls) -> None:
        """Create all tables based on the imported models."""
        try:
            # Import models so that SQLModel knows them
            from .models import Location, UserSettings, WeatherRecord  # noqa: F401

            SQLModel.metadata.create_all(cls.get_engine())
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    @classmethod
    def get_engine(cls) -> Engine:
        """Return the database engine, initializing if needed."""
        if cls._engine is None:
            cls._initialize_db()
        assert cls._engine is not None, "Database engine not initialized"
        return cls._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context-managed session generator."""
        with Session(self.get_engine()) as session:
            yield session

    @classmethod
    def get_database_path(cls) -> str:
        """Return the database path or URL."""
        return str(DATABASE_URL)


def init_db() -> "Database":
    """Initialize the database and create tables."""
    try:
        db: Database = Database()
        db.create_tables()
        logger.info("Database initialized successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Yield a session using the global database engine."""
    with Session(Database.get_engine()) as session:
        yield session
