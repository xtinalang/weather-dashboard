from typing import Literal, TypedDict

# Temperature unit type used across modules (for now)
TemperatureUnit = Literal["C", "F"]


# Shared condition structure
class WeatherCondition(TypedDict, total=False):
    text: str
    icon: str
    code: int


# Current weather data (from /current.json or /forecast.json "current")
class CurrentWeather(TypedDict, total=False):
    last_updated: str
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    condition: WeatherCondition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    is_day: int
    uv: float
    gust_mph: float
    gust_kph: float


# Location data
class LocationData(TypedDict, total=False):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


# Forecast: day-level detail
class DayForecast(TypedDict, total=False):
    maxtemp_c: float
    maxtemp_f: float
    mintemp_c: float
    mintemp_f: float
    avgtemp_c: float
    avgtemp_f: float
    maxwind_mph: float
    maxwind_kph: float
    totalprecip_mm: float
    totalprecip_in: float
    totalsnow_cm: float
    avgvis_km: float
    avgvis_miles: float
    avghumidity: int
    daily_will_it_rain: int
    daily_chance_of_rain: int
    daily_will_it_snow: int
    daily_chance_of_snow: int
    condition: WeatherCondition
    uv: float


# Astro data (sunrise, moonset, etc.)
class AstroInfo(TypedDict, total=False):
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: str
    is_moon_up: int
    is_sun_up: int


# One day's forecast
class ForecastDay(TypedDict, total=False):
    date: str
    date_epoch: int
    day: DayForecast
    astro: AstroInfo


# Forecast list for forecast day
class ForecastDays(TypedDict):
    forecastday: list[ForecastDay]


# Forecast data for forecast data
class ForecastData(TypedDict, total=False):
    forecast: ForecastDays


# Weather data for weather from /current.json or /forecast.json "current" or "forecast"
class WeatherData(TypedDict, total=False):
    location: LocationData
    current: CurrentWeather
    forecast: ForecastDays | None


# Weather response for weather from /current.json or /forecast.json "current" or "forecast"
class WeatherResponse(TypedDict, total=False):
    location: LocationData
    current: CurrentWeather
    forecast: ForecastData
