import os
from pathlib import Path

from decouple import config


# Get the user's data directory based on OS
def get_user_data_dir() -> Path:
    """Get the appropriate user data directory based on the operating system."""
    if os.name == "nt":  # Windows
        data_dir = Path(os.environ.get("APPDATA", "~")) / "weather-dashboard"
    else:  # Unix-like (Linux, macOS)
        data_dir = Path.home() / ".local" / "share" / "weather-dashboard"

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# Default database path for packaged installations
DEFAULT_DB_PATH = get_user_data_dir() / "weather_app.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

# Load DATABASE_URL with fallback to default
DATABASE_URL = config("DATABASE_URL", default=DEFAULT_DATABASE_URL, cast=str)

# Optional: Provide other configuration with fallbacks
WEATHER_API_KEY = config("WEATHER_API_KEY", default="")
SECRET_KEY = config("SECRET_KEY", default="dev-key-change-in-production")


class Config:
    """Configuration class for the weather application."""

    def __init__(self) -> None:
        self.database_url = DATABASE_URL
        self.weather_api_key = WEATHER_API_KEY
        self.secret_key = SECRET_KEY
        self.data_dir = get_user_data_dir()

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return bool(self.database_url.startswith("sqlite"))

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL database."""
        return bool(self.database_url.startswith("postgresql"))

    def get_database_path(self) -> Path | None:
        """Get the database file path if using SQLite."""
        if self.is_sqlite:
            # Extract path from sqlite:///path format
            path_str = self.database_url.replace("sqlite:///", "")
            return Path(path_str)
        return None


# Global config instance
config_instance = Config()
