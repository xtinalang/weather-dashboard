#!/usr/bin/env python
"""
Database migration script to update the schema with new fields.
Specifically adds the forecast_days column to the UserSettings table.
"""

import datetime
import logging
import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import text

from weather_app.database import Database

# Add parent directory to path to import weather_app modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("database_migration")


def migrate_database():
    """Add missing columns to existing tables"""
    try:
        logger.info("Starting database migration...")

        # Get database connection
        db = Database()
        db_path = Path(db.get_database_path())

        if not db_path.exists():
            logger.error(f"Database not found at {db_path}")
            print(f"❌ Database file not found at {db_path}")
            return False

        # Create a connection and run raw SQL to add the missing column
        with db.get_session() as session:
            # Check if column exists
            check_column_sql = text("PRAGMA table_info(usersettings)")
            columns = session.execute(check_column_sql)
            column_names = [column[1] for column in columns]

            # Add forecast_days column if not present
            if "forecast_days" not in column_names:
                logger.info("Adding 'forecast_days' column to UserSettings table")
                add_column_sql = text(
                    "ALTER TABLE usersettings ADD COLUMN forecast_days INTEGER DEFAULT 7"
                )
                session.execute(add_column_sql)
                session.commit()
                logger.info("Successfully added forecast_days column")
                print(
                    "✅ Successfully added 'forecast_days' column to UserSettings table"
                )
            else:
                logger.info(
                    "The 'forecast_days' column already exists in UserSettings table"
                )
                print(
                    "ℹ️ The 'forecast_days' column already exists in UserSettings table"
                )

            # Verify the column was added correctly
            verify_sql = text("SELECT * FROM usersettings LIMIT 1")
            result = session.execute(verify_sql).first()

            if result:
                settings_dict = dict(result._mapping)
                logger.info(f"Current settings: {settings_dict}")

                # Check if forecast_days has a value
                if "forecast_days" in settings_dict:
                    forecast_days = settings_dict["forecast_days"]
                    if forecast_days is None:
                        # Set default value if null
                        logger.info("Setting default value for forecast_days")
                        update_sql = text(
                            "UPDATE usersettings SET forecast_days = 7 WHERE forecast_days IS NULL"
                        )
                        session.execute(update_sql)
                        session.commit()
                        print("✅ Set default value (7) for forecast_days")
                    # Update any existing forecast_days values of 5 to 7 as part of the standard change
                    elif forecast_days == 5:
                        logger.info(
                            "Updating forecast_days from 5 to 7 to match new default"
                        )
                        update_sql = text(
                            "UPDATE usersettings SET forecast_days = 7 WHERE forecast_days = 5"
                        )
                        session.execute(update_sql)
                        session.commit()
                        print(
                            "✅ Updated forecast_days from 5 to 7 to match new application default"
                        )

            return True
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"❌ Migration failed: {e}")
        return False


def create_backup():
    """Create a backup of the database before migration"""
    try:
        db_path = Path(Database.get_database_path())
        if not db_path.exists():
            logger.error(f"Database not found at {db_path}")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.with_name(f"weather_backup_{timestamp}.db")

        shutil.copy2(db_path, backup_path)
        logger.info(f"Created database backup at {backup_path}")
        print(f"✅ Created database backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        print(f"❌ Backup failed: {e}")
        return False


if __name__ == "__main__":
    print("📊 Weather App Database Migration")
    print("=" * 40)

    # Create backup first
    print("\n🔄 Creating database backup...")
    if create_backup():
        # Run migration
        print("\n🔄 Running database migration...")
        if migrate_database():
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed. See migration.log for details.")
    else:
        print("\n❌ Backup failed. Migration aborted.")
