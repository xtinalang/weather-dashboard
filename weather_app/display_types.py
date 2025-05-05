from typing import Any, Dict, Optional, TypedDict


class LocationData(TypedDict):
    """Type definition for location data returned from the API"""

    name: str
    lat: float
    lon: float
    country: str
    region: Optional[str]
    url: Optional[str]


class ConditionData(TypedDict):
    """Type definition for weather condition data"""

    text: str
    code: int


class CurrentWeatherData(TypedDict):
    """Type definition for current weather data returned from the API"""

    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    humidity: int
    pressure_mb: float
    pressure_in: float
    wind_kph: float
    wind_mph: float
    wind_dir: str
    vis_km: float
    vis_miles: float
    precip_mm: float
    precip_in: float
    last_updated: str
    condition: ConditionData


class WeatherData(TypedDict):
    """Type definition for complete weather data including forecast"""

    location: Dict[str, Any]
    current: CurrentWeatherData
    forecast: Optional[Dict[str, Any]]
