from typing import Any, Dict, List, Literal, Optional, TypedDict

# Temperature unit type used across modules
TemperatureUnit = Literal["C", "F"]


class WeatherCondition(TypedDict, total=False):
    """Type definition for weather condition data"""

    text: str
    icon: str
    code: int


class CurrentWeather(TypedDict, total=False):
    """Type definition for current weather data"""

    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    humidity: int
    pressure_mb: float
    wind_kph: float
    wind_mph: float
    wind_dir: str
    condition: WeatherCondition


class WeatherData(TypedDict, total=False):
    """Type definition for complete weather data including forecast"""

    current: CurrentWeather
    location: Dict[str, Any]
    forecast: Optional[Dict[str, Any]]


class ForecastDay(TypedDict, total=False):
    """Type definition for a single day's forecast"""

    date: str
    day: Dict[str, Any]
    astro: Dict[str, str]


class ForecastDays(TypedDict):
    """Type definition for multiple days of forecast"""

    forecastday: List[ForecastDay]


class ForecastData(TypedDict, total=False):
    """Type definition for forecast data"""

    forecast: ForecastDays
