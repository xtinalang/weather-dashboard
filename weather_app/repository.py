import logging
from datetime import datetime, timedelta
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.sql.expression import func
from sqlmodel import Session, SQLModel, col, or_, select

from weather_app.database import Database
from weather_app.exceptions import DatabaseError
from weather_app.exceptions import DetachedInstanceError as AppDetachedError
from weather_app.models import Location, UserSettings, WeatherRecord

# Generic type variable for models
T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""

    model_class: type[T]

    def __init__(self) -> None:
        self.db = Database()

    def create(self, obj: T) -> T:
        """Create a new database record"""
        with Session(Database.get_engine()) as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def get_by_id(self, id: int) -> Optional[T]:
        """Get a record by ID"""
        try:
            with self.db.get_session() as session:
                return session.get(self.model_class, id)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get {self.model_class.__name__} by ID: {e}"
            raise DatabaseError(error_msg) from e

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Get all records with pagination"""
        try:
            with self.db.get_session() as session:
                statement = select(self.model_class).offset(offset).limit(limit)
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get all {self.model_class.__name__}s: {e}"
            raise DatabaseError(error_msg) from e

    def update(self, id: int, data: dict[str, Any]) -> Optional[T]:
        """Update a record by ID with the provided data"""
        try:
            with self.db.get_session() as session:
                obj = session.get(self.model_class, id)
                if not obj:
                    return None

                for key, value in data.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)

                # Update timestamp if the model has this field
                if hasattr(obj, "updated_at"):
                    obj.updated_at = datetime.now()

                session.add(obj)
                session.commit()
                session.refresh(obj)
                return obj
        except SQLAlchemyError as e:
            error_msg = f"Failed to update {self.model_class.__name__}: {e}"
            raise DatabaseError(error_msg) from e

    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        try:
            with self.db.get_session() as session:
                obj = session.get(self.model_class, id)
                if not obj:
                    return False

                session.delete(obj)
                session.commit()
                return True
        except SQLAlchemyError as e:
            error_msg = f"Failed to delete {self.model_class.__name__}: {e}"
            raise DatabaseError(error_msg) from e

    def count(self) -> int:
        """Count all records"""
        try:
            with self.db.get_session() as session:
                statement = select(func.count()).select_from(self.model_class)
                return session.exec(statement).one()
        except SQLAlchemyError as e:
            error_msg = f"Failed to count {self.model_class.__name__}s: {e}"
            raise DatabaseError(error_msg) from e


class LocationRepository(BaseRepository[Location]):
    """Repository for Location entity operations"""

    model_class = Location

    def search(self, query: str, limit: int = 10) -> list[Location]:
        """Search locations by name, region, or country"""
        try:
            search_term = f"%{query}%"
            with self.db.get_session() as session:
                statement = (
                    select(Location)
                    .where(
                        or_(
                            col(Location.name).ilike(search_term),
                            col(Location.country).ilike(search_term),
                            col(Location.region).ilike(search_term),
                        )
                    )
                    .limit(limit)
                )
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to search locations: {e}"
            raise DatabaseError(error_msg) from e

    def get_favorites(self) -> list[Location]:
        """Get favorite locations"""
        try:
            with self.db.get_session() as session:
                statement = select(Location).where(Location.is_favorite.is_(True))
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get favorite locations: {e}"
            raise DatabaseError(error_msg) from e

    def find_by_coordinates(
        self, latitude: float, longitude: float, threshold: float = 0.01
    ) -> Optional[Location]:
        """Find location by approximate coordinates within a threshold"""

        logger = logging.getLogger("weather_app")

        logger.debug(
            f"Searching for location with coordinates: {latitude}, {longitude} "
            f"(threshold: {threshold})"
        )

        try:
            with self.db.get_session() as session:
                # Log SQL parameters
                logger.debug(
                    f"SQL parameters: latitude={latitude}, longitude={longitude}, "
                    f"threshold={threshold}"
                )

                # Try a more flexible search with progressive thresholds
                location = None

                # Try exact match first (faster)
                statement = (
                    select(Location)
                    .where(
                        (Location.latitude == latitude)
                        & (Location.longitude == longitude)
                    )
                    .limit(1)
                )
                location = session.exec(statement).first()

                # If not found, try with threshold
                if not location:
                    statement = (
                        select(Location)
                        .where(
                            (func.abs(Location.latitude - latitude) < threshold)
                            & (func.abs(Location.longitude - longitude) < threshold)
                        )
                        .limit(1)
                    )
                    location = session.exec(statement).first()

                # Log search results
                if location:
                    logger.debug(
                        f"Found location: {location.name} (ID: {location.id}) "
                        f"at {location.latitude}, {location.longitude}"
                    )

                    # Create a copy with all required attributes to avoid session issues
                    return self._create_detached_location_copy(location)
                else:
                    logger.debug(
                        f"No location found with coordinates {latitude}, {longitude} "
                        f"(threshold: {threshold})"
                    )

                    # If no match with threshold, log available locations for debugging
                    all_locations_stmt = select(Location).limit(5)
                    sample_locations = session.exec(all_locations_stmt).all()
                    if sample_locations:
                        logger.debug(
                            f"Sample locations in database "
                            f"({len(sample_locations)} shown):"
                        )
                        for loc in sample_locations:
                            logger.debug(
                                f"  - {loc.name} (ID: {loc.id}): "
                                f"{loc.latitude}, {loc.longitude}"
                            )
                    else:
                        logger.debug("No locations exist in database")

                    return None

        except DetachedInstanceError as e:
            error_msg = f"Session error finding location by coordinates: {e}"
            logger.error(error_msg)
            raise AppDetachedError(error_msg) from e
        except SQLAlchemyError as e:
            error_msg = f"Database error finding location by coordinates: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error finding location by coordinates: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def find_or_create_by_coordinates(
        self,
        name: str,
        latitude: float,
        longitude: float,
        country: str = "Unknown",
        region: Optional[str] = None,
    ) -> Location:
        """Find a location by coordinates or create it if it doesn't exist"""

        logger = logging.getLogger("weather_app")

        # First try to find by coordinates
        location = self.find_by_coordinates(latitude, longitude)
        if location:
            return location

        # If not found, create a new location
        logger.debug(f"Creating new location: {name} at {latitude}, {longitude}")

        try:
            # Create the new location within a session
            with self.db.get_session() as session:
                new_location = Location(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    country=country,
                    region=region,
                    is_favorite=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                # Save to database
                session.add(new_location)
                session.commit()
                session.refresh(new_location)

                logger.debug(
                    f"Created new location: {new_location.name} (ID: {new_location.id})"
                )

                # Return a detached copy to avoid session issues
                return self._create_detached_location_copy(new_location)

        except Exception as e:
            error_msg = f"Failed to create location: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _create_detached_location_copy(self, location: Location) -> Location:
        """Create a detached copy of a location to avoid session issues"""

        # Create a new instance with all the data from the original
        try:
            detached_copy = Location(
                id=location.id,
                name=location.name,
                latitude=location.latitude,
                longitude=location.longitude,
                country=location.country,
                region=location.region,
                is_favorite=location.is_favorite,
                created_at=getattr(location, "created_at", datetime.now()),
                updated_at=datetime.now(),
            )
            return detached_copy
        except Exception as e:
            # If any attributes are missing, log and fall back to minimal copy

            logger = logging.getLogger("weather_app")
            logger.warning(
                f"Error creating full detached copy: {e}, falling back to minimal copy"
            )

            return Location(
                id=location.id if hasattr(location, "id") else None,
                name=location.name if hasattr(location, "name") else "Unknown",
                latitude=location.latitude if hasattr(location, "latitude") else 0.0,
                longitude=location.longitude if hasattr(location, "longitude") else 0.0,
                country=location.country if hasattr(location, "country") else "Unknown",
                region=None,
                is_favorite=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class WeatherRepository(BaseRepository[WeatherRecord]):
    """Repository for WeatherRecord entity operations"""

    model_class = WeatherRecord

    def get_by_location(self, location_id: int, limit: int = 10) -> list[WeatherRecord]:
        """Get weather records for a specific location"""
        try:
            with self.db.get_session() as session:
                statement = (
                    select(WeatherRecord)
                    .where(WeatherRecord.location_id == location_id)
                    .order_by(WeatherRecord.timestamp.desc())
                    .limit(limit)
                )
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get weather records by location: {e}"
            raise DatabaseError(error_msg) from e

    def get_records_since(self, days: int = 7) -> list[WeatherRecord]:
        """Get weather records from the past X days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        try:
            with self.db.get_session() as session:
                statement = (
                    select(WeatherRecord)
                    .where(WeatherRecord.timestamp >= cutoff_date)
                    .order_by(WeatherRecord.timestamp.desc())
                )
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get recent weather records: {e}"
            raise DatabaseError(error_msg) from e

    def get_latest_for_location(self, location_id: int) -> Optional[WeatherRecord]:
        """Get the most recent weather record for a location"""
        try:
            with self.db.get_session() as session:
                statement = (
                    select(WeatherRecord)
                    .where(WeatherRecord.location_id == location_id)
                    .order_by(WeatherRecord.timestamp.desc())
                    .limit(1)
                )
                return session.exec(statement).first()
        except SQLAlchemyError as e:
            error_msg = f"Failed to get latest weather record: {e}"
            raise DatabaseError(error_msg) from e


class SettingsRepository(BaseRepository[UserSettings]):
    """Repository for UserSettings entity operations"""

    model_class = UserSettings

    def get_settings(self) -> UserSettings:
        """Get application settings, creating default settings if none exist"""

        logger = logging.getLogger("weather_app")

        try:
            with self.db.get_session() as session:
                # Get the first/only settings record (ID=1)
                settings = session.get(UserSettings, 1)

                # Create default settings if none exist
                if settings is None:
                    logger.info("Creating default settings")
                    settings = UserSettings(
                        id=1,  # Explicitly set ID to 1
                        temperature_unit="celsius",
                        wind_speed_unit="m/s",
                        save_history=True,
                        max_history_days=7,
                        theme="default",
                        forecast_days=7,  # Default forecast days
                    )
                    session.add(settings)
                    session.commit()
                    session.refresh(settings)

                # Create a detached copy to avoid session issues
                detached_settings = self._create_detached_settings_copy(settings)
                logger.debug(
                    f"Retrieved settings: temp={detached_settings.temperature_unit}, "
                    f"forecast_days={detached_settings.forecast_days}"
                )
                return detached_settings

        except (SQLAlchemyError, DetachedInstanceError) as e:
            error_msg = f"Failed to get application settings: {e}"
            logger.error(error_msg)

            # Return default settings as fallback
            logger.info("Returning default settings due to error")
            return self._create_default_settings()
        except Exception as e:
            error_msg = f"Unexpected error getting settings: {e}"
            logger.error(error_msg)
            return self._create_default_settings()

    def update_temperature_unit(self, unit: str) -> UserSettings:
        """Update temperature unit preference"""

        logger = logging.getLogger("weather_app")

        try:
            with self.db.get_session() as session:
                # Get settings directly in this session
                settings = session.get(UserSettings, 1)

                # Create if doesn't exist
                if settings is None:
                    settings = UserSettings(
                        id=1,
                        temperature_unit=unit.lower(),
                        wind_speed_unit="m/s",
                        save_history=True,
                        max_history_days=7,
                        theme="default",
                        forecast_days=7,
                    )
                else:
                    settings.temperature_unit = unit.lower()

                session.add(settings)
                session.commit()
                session.refresh(settings)

                # Create a detached copy to return
                detached_settings = self._create_detached_settings_copy(settings)
                logger.debug(
                    f"Updated temperature unit to {detached_settings.temperature_unit}"
                )
                return detached_settings

        except SQLAlchemyError as e:
            error_msg = f"Failed to update temperature unit: {e}"
            logger.error(error_msg)

            # Return default settings with the requested unit
            default_settings = self._create_default_settings()
            default_settings.temperature_unit = unit.lower()
            return default_settings

    def _create_detached_settings_copy(self, settings: UserSettings) -> UserSettings:
        """Create a detached copy of settings to avoid session issues"""
        try:
            return UserSettings(
                id=settings.id,
                temperature_unit=settings.temperature_unit,
                wind_speed_unit=settings.wind_speed_unit,
                save_history=settings.save_history,
                max_history_days=settings.max_history_days,
                theme=settings.theme,
                forecast_days=settings.forecast_days,
                default_location_id=getattr(settings, "default_location_id", None),
            )
        except Exception as e:
            # If error creating copy, return default settings

            logger = logging.getLogger("weather_app")
            logger.error(f"Error creating settings copy: {e}, falling back to defaults")
            return self._create_default_settings()

    def _create_default_settings(self) -> UserSettings:
        """Create default settings object"""
        return UserSettings(
            id=1,
            temperature_unit="celsius",
            wind_speed_unit="m/s",
            save_history=True,
            max_history_days=7,
            theme="default",
            forecast_days=7,
        )
