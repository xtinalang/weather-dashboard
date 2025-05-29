#!/usr/bin/env python
"""
Utility script to initialize the weather app database directly.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlmodel import select

from weather_app.database import DATABASE_URL
from weather_app.database import init_db as initialize_database
from weather_app.models import Location
from weather_app.repository import LocationRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("weather_app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("database_init")


def init_database():
    """Initialize the database"""
    try:
        logger.info("Initializing database...")
        initialize_database()
        logger.info("Database initialized successfully!")
        print("✅ Database initialized successfully!")

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            print(f"Database location: {db_path}")

            # Ensure the file exists
            path = Path(db_path)
            if path.exists():
                size = path.stat().st_size
                print(f"Database file size: {size / 1024:.1f} KB")
            else:
                print(f"Warning: Database file doesn't exist at {db_path}")
        else:
            print(f"Database URL: {DATABASE_URL}")

    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        print(f"❌ Error initializing database: {e}")
        return False

    return True


def create_sample_location():
    """Create a sample location in the database"""
    try:
        # Create sample location
        repo = LocationRepository()

        # Check if Paris already exists using direct SQL access
        with repo.db.get_session() as session:
            # Search for Paris
            query = select(Location).where(Location.name == "Paris")
            results = session.exec(query).all()

            if results:
                print(f"Sample location already exists: {results[0].name}")
                return True

            # Paris doesn't exist, create it
            sample = Location(
                name="Paris",
                country="France",
                region="Île-de-France",
                latitude=48.8566,
                longitude=2.3522,
                is_favorite=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Add to session
            session.add(sample)
            session.commit()
            session.refresh(sample)

            print(f"✅ Created sample location: {sample.name} (ID: {sample.id})")
            return True

    except Exception as e:
        logger.error(f"Error creating sample location: {e}", exc_info=True)
        print(f"❌ Error creating sample location: {e}")
        return False


if __name__ == "__main__":
    print("💾 Initializing Weather App Database...")
    if init_database():
        print("\n🌍 Creating sample location...")
        create_sample_location()
        print("\n✨ Database setup complete! You can now run the weather app.")
    else:
        print("\n❌ Database initialization failed. Please check the logs.")
