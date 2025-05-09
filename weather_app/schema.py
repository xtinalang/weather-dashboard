from typing import List, Literal, Optional, TypedDict

# Temperature unit type used across modules (for now)
TemperatureUnit = Literal["C", "F"]


# Shared condition structure
class WeatherCondition(TypedDict, total=False):
    text: str
    icon: str
    code: int


# Current weather data (from /current.json or /forecast.json "current")
class CurrentWeather(TypedDict, total=False):
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
    condition: WeatherCondition


# Location data
class LocationData(TypedDict, total=False):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime: str


# Forecast: day-level detail
class DayForecast(TypedDict, total=False):
    maxtemp_c: float
    mintemp_c: float
    avgtemp_c: float
    maxwind_kph: float
    totalprecip_mm: float
    avghumidity: float
    condition: WeatherCondition


# Astro data (sunrise, moonset, etc.)
class AstroData(TypedDict, total=False):
    sunrise: str
    sunset: str
    # moonrise: str
    # moonset: str
    # moon_phase: str
    # moon_illumination: str


# One day's forecast
class ForecastDay(TypedDict, total=False):
    date: str
    date_epoch: int
    day: DayForecast
    astro: AstroData


# Forecast list for forecast day
class ForecastDays(TypedDict):
    forecastday: List[ForecastDay]


# class ForecastData(TypedDict, total=False):
#     forecast: ForecastDays


# class ConditionData(TypedDict):
#     text: str
#     code: int


# class CurrentWeatherData(TypedDict):
#     temp_c: float
#     temp_f: float
#     feelslike_c: float
#     feelslike_f: float
#     humidity: int
#     pressure_mb: float
#     pressure_in: float
#     wind_kph: float
#     wind_mph: float
#     wind_dir: str
#     vis_km: float
#     vis_miles: float
#     precip_mm: float
#     precip_in: float
#     last_updated: str
#     condition: ConditionData


# class WeatherData(TypedDict, total=False):
#     current: CurrentWeather
#     location: Dict[str, Any]
#     forecast: Optional[ForcastDays]
class WeatherData(TypedDict, total=False):
    location: LocationData
    current: CurrentWeather
    forecast: Optional[ForecastDays]
