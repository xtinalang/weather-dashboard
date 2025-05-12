from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # This prevents circular imports while still enabling proper type checking
    pass


class Location(SQLModel, table=True):
    """
    Represents a geographical location for weather data.

    Attributes:
        id: Primary key identifier
        name: Name of the location (city, area, etc.)
        latitude: Geographical latitude
        longitude: Geographical longitude
        country: Country where the location is situated
        region: Region or state within the country
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
        is_favorite: Whether this location is marked as a favorite
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    latitude: float
    longitude: float
    country: str = Field(index=True)
    region: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_favorite: bool = Field(default=False, index=True)

    # Relationships
    weather_records: List["WeatherRecord"] = Relationship(back_populates="location")

    def __repr__(self) -> str:
        """
        Get string representation of the location.

        Returns:
            String in format "name, region country"
        """
        return f"{self.name}, {self.region or ''} {self.country}"

    def coordinates(self) -> tuple[float, float]:
        """
        Returns a tuple of (latitude, longitude).

        Returns:
            Tuple containing latitude and longitude
        """
        return (self.latitude, self.longitude)

    def to_dict(self) -> Dict[str, object]:
        """
        Convert the model to a dictionary.

        Returns:
            Dictionary representation of the location
        """
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "region": self.region,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_favorite": self.is_favorite,
        }


class WeatherRecord(SQLModel, table=True):
    """
    Stores historical weather data for a location.

    Attributes:
        id: Primary key identifier
        location_id: Foreign key to the location
        timestamp: When the weather data was recorded
        temperature: Temperature in Celsius
        feels_like: "Feels like" temperature in Celsius
        humidity: Relative humidity percentage
        pressure: Atmospheric pressure in millibars
        wind_speed: Wind speed in km/h
        wind_direction: Direction of the wind
        condition: Short description of weather condition
        condition_description: Longer description of weather condition
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="location.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    temperature: float
    feels_like: Optional[float] = Field(default=None)
    humidity: Optional[int] = Field(default=None)
    pressure: Optional[float] = Field(default=None)
    wind_speed: Optional[float] = Field(default=None)
    wind_direction: Optional[str] = Field(default=None)
    condition: str
    condition_description: Optional[str] = Field(default=None)

    # Relationships
    location: Location = Relationship(back_populates="weather_records")

    def to_dict(self) -> Dict[str, object]:
        """
        Convert the model to a dictionary.

        Returns:
            Dictionary representation of the weather record
        """
        return {
            "id": self.id,
            "location_id": self.location_id,
            "timestamp": self.timestamp,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "condition": self.condition,
            "condition_description": self.condition_description,
        }


class UserSettings(SQLModel, table=True):
    """
    User preferences for the weather application.

    Attributes:
        id: Primary key identifier, default is 1 for single settings record
        temperature_unit: Unit for temperature display (celsius, fahrenheit)
        wind_speed_unit: Unit for wind speed display (m/s, km/h, mph)
        default_location_id: Foreign key to default location if set
        save_history: Whether to save historical weather data
        max_history_days: Maximum days to keep historical data
        theme: UI theme preference
        forecast_days: Default number of forecast days to display
    """

    id: int = Field(default=1, primary_key=True)  # Only one settings record
    temperature_unit: str = Field(default="celsius")  # celsius, fahrenheit
    wind_speed_unit: str = Field(default="m/s")  # m/s, km/h, mph
    default_location_id: Optional[int] = Field(default=None, foreign_key="location.id")
    save_history: bool = Field(default=True)
    max_history_days: int = Field(default=7)
    theme: str = Field(default="default")  # default, dark, light
    forecast_days: int = Field(default=7)  # default number of forecast days

    # Relationship to default location
    default_location: Optional[Location] = Relationship()

    def to_dict(self) -> Dict[str, object]:
        """
        Convert the model to a dictionary.

        Returns:
            Dictionary representation of the user settings
        """
        return {
            "id": self.id,
            "temperature_unit": self.temperature_unit,
            "wind_speed_unit": self.wind_speed_unit,
            "default_location_id": self.default_location_id,
            "save_history": self.save_history,
            "max_history_days": self.max_history_days,
            "theme": self.theme,
            "forecast_days": self.forecast_days,
        }
