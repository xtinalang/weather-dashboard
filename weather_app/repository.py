from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func
from sqlmodel import SQLModel, col, or_, select

from weather_app.database import Database
from weather_app.exceptions import DatabaseError
from weather_app.models import Location, UserSettings, WeatherRecord

# Generic type variable for models
T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""

    model_class: Type[T]

    def __init__(self) -> None:
        self.db = Database()

    def create(self, obj: T) -> T:
        """Create a new database record"""
        try:
            with self.db.session() as session:
                session.add(obj)
                session.commit()
                session.refresh(obj)
                return obj
        except SQLAlchemyError as e:
            error_msg = f"Failed to create {self.model_class.__name__}: {e}"
            raise DatabaseError(error_msg) from e

    def get_by_id(self, id: int) -> Optional[T]:
        """Get a record by ID"""
        try:
            with self.db.session() as session:
                return session.get(self.model_class, id)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get {self.model_class.__name__} by ID: {e}"
            raise DatabaseError(error_msg) from e

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination"""
        try:
            with self.db.session() as session:
                statement = select(self.model_class).offset(offset).limit(limit)
                results = session.exec(statement).all()
                return list(results)
        except SQLAlchemyError as e:
            error_msg = f"Failed to get all {self.model_class.__name__}s: {e}"
            raise DatabaseError(error_msg) from e

    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update a record by ID with the provided data"""
        try:
            with self.db.session() as session:
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
            with self.db.session() as session:
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
            with self.db.session() as session:
                statement = select(func.count()).select_from(self.model_class)
                return session.exec(statement).one()
        except SQLAlchemyError as e:
            error_msg = f"Failed to count {self.model_class.__name__}s: {e}"
            raise DatabaseError(error_msg) from e


class LocationRepository(BaseRepository[Location]):
    """Repository for Location entity operations"""

    model_class = Location

    def search(self, query: str, limit: int = 10) -> List[Location]:
        """Search locations by name, region, or country"""
        try:
            search_term = f"%{query}%"
            with self.db.session() as session:
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

    def get_favorites(self) -> List[Location]:
        """Get favorite locations"""
        try:
            with self.db.session() as session:
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
        try:
            with self.db.session() as session:
                statement = (
                    select(Location)
                    .where(
                        (func.abs(Location.latitude - latitude) < threshold)
                        & (func.abs(Location.longitude - longitude) < threshold)
                    )
                    .limit(1)
                )
                return session.exec(statement).first()
        except SQLAlchemyError as e:
            error_msg = f"Failed to find location by coordinates: {e}"
            raise DatabaseError(error_msg) from e


class WeatherRepository(BaseRepository[WeatherRecord]):
    """Repository for WeatherRecord entity operations"""

    model_class = WeatherRecord

    def get_by_location(self, location_id: int, limit: int = 10) -> List[WeatherRecord]:
        """Get weather records for a specific location"""
        try:
            with self.db.session() as session:
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

    def get_records_since(self, days: int = 7) -> List[WeatherRecord]:
        """Get weather records from the past X days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        try:
            with self.db.session() as session:
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
            with self.db.session() as session:
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
        try:
            with self.db.session() as session:
                # Get the first/only settings record (ID=1)
                statement = select(UserSettings)
                settings = session.exec(statement).first()

                # Create default settings if none exist
                if settings is None:
                    settings = UserSettings()
                    session.add(settings)
                    session.commit()
                    session.refresh(settings)

                return settings
        except SQLAlchemyError as e:
            error_msg = f"Failed to get application settings: {e}"
            raise DatabaseError(error_msg) from e

    def update_temperature_unit(self, unit: str) -> UserSettings:
        """Update temperature unit preference"""
        try:
            with self.db.session() as session:
                settings = self.get_settings()
                settings.temperature_unit = unit.lower()
                session.add(settings)
                session.commit()
                session.refresh(settings)
                return settings
        except SQLAlchemyError as e:
            error_msg = f"Failed to update temperature unit: {e}"
            raise DatabaseError(error_msg) from e
