"""
Test constants and shared data for the Weather Dashboard Playwright tests.
Contains all repeated values, coordinates, and test data used across test files.
"""

# =============================================================================
# Location Constants
# =============================================================================

# Test Coordinates (London)
LONDON_LAT = 51.5074
LONDON_LON = -0.1278
LONDON_COORDINATES = f"{LONDON_LAT}/{LONDON_LON}"

# Popular Cities for Quick Links
POPULAR_CITIES = ["London", "New York", "Tokyo", "Sydney"]

# Test Location Names
TEST_CITY_LONDON = "London"
TEST_CITY_NEW_YORK = "New York"
TEST_CITY_TOKYO = "Tokyo"
TEST_CITY_PARIS = "Paris"
TEST_CITY_SYDNEY = "Sydney"

# =============================================================================
# Weather Data Constants
# =============================================================================

# Wind Directions
WIND_DIRECTIONS = [
    "N",
    "S",
    "E",
    "W",
    "NE",
    "NW",
    "SE",
    "SW",
    "NNE",
    "NNW",
    "ENE",
    "ESE",
    "SSE",
    "SSW",
    "WSW",
    "WNW",
]

# Weather Units
UNIT_CELSIUS = "C"
UNIT_FAHRENHEIT = "F"
DEGREE_CELSIUS = "°C"
DEGREE_FAHRENHEIT = "°F"

# Weather Metrics Units
HUMIDITY_UNIT = "%"
PRESSURE_UNIT = "mb"
PRECIPITATION_UNIT = "mm"
WIND_SPEED_UNITS = ["km/h", "mph", "kph"]

# =============================================================================
# Test Query Strings
# =============================================================================

# Natural Language Queries
NL_QUERY_LONDON_TODAY = "What's the weather like in London today?"
NL_QUERY_PARIS_TOMORROW = "How's the weather in Paris tomorrow?"
NL_QUERY_NYC_WEEKEND = "Weather for New York this weekend?"
NL_QUERY_TOKYO_MONDAY = "What's Tokyo weather like next Monday?"
NL_QUERY_COMPARE_CITIES = "Compare weather between London and Paris tomorrow"
NL_QUERY_INVALID = "weather stuff sometime maybe"

# Search Queries
SEARCH_QUERY_LONDON = "London"
SEARCH_QUERY_SPRINGFIELD = "Springfield"
SEARCH_QUERY_INVALID = "NonExistentCityName12345"
SEARCH_QUERY_INTERNATIONAL = "München"  # Munich in German
SEARCH_QUERY_SPECIAL_CHARS = "São Paulo"
SEARCH_QUERY_COORDINATES = "51.5074,-0.1278"  # London coordinates

# Case Variations for Testing
CASE_VARIATIONS = ["london", "LONDON", "London", "LoNdOn"]

# =============================================================================
# Form Placeholders and Labels
# =============================================================================

PLACEHOLDER_ENTER_CITY = "Enter city name"
PLACEHOLDER_LOCATION_EXAMPLES = "Enter city name (e.g., London, New York)"
PLACEHOLDER_NL_EXAMPLES = (
    "e.g., What's the weather like in London tomorrow? "
    "Weather for Paris this weekend? How's Tokyo next Monday?"
)

# =============================================================================
# Invalid Test Data
# =============================================================================

# Invalid Coordinates
INVALID_COORDINATES_999 = "999/999"
INVALID_COORDINATES_0 = "0/0"  # Null Island

# =============================================================================
# Viewport Sizes for Responsive Testing
# =============================================================================

VIEWPORT_DESKTOP = {"width": 1200, "height": 800}
VIEWPORT_TABLET = {"width": 768, "height": 1024}
VIEWPORT_MOBILE = {"width": 375, "height": 667}

# =============================================================================
# Forecast Options
# =============================================================================

FORECAST_DAYS_OPTIONS = [1, 3, 5, 7]
DEFAULT_FORECAST_DAYS = 3

# =============================================================================
# URL Patterns and Endpoints
# =============================================================================

# URL Path Components
PATH_WEATHER = "weather"
PATH_FORECAST = "forecast"
PATH_SEARCH = "search"
PATH_NL_DATE_WEATHER = "nl-date-weather"
PATH_API_WEATHER = "api/weather"

# =============================================================================
# CSS Selectors and Locators
# =============================================================================

# Common CSS Classes
CSS_CLASS_TEMPERATURE = ".temperature"
CSS_CLASS_CONDITION = ".condition"
CSS_CLASS_WEATHER_DETAILS = ".weather-details"
CSS_CLASS_FORECAST_DAY = ".forecast-day"
CSS_CLASS_FLASH_MESSAGES = ".flash-messages"
CSS_CLASS_NAV = ".nav"
CSS_CLASS_CARD = ".card"
CSS_CLASS_ROW = ".row"

# Form Selectors
FORM_SEARCH = "form[action*='search']"
FORM_NL_WEATHER = "form[action*='nl_date_weather']"
FORM_FORECAST = "form[action*='forecast_form']"
FORM_TOGGLE_FAVORITE = "form[action*='toggle_favorite']"

# Input Selectors
INPUT_QUERY = "input[name='query']"
INPUT_LOCATION = "input[name='location']"
INPUT_CSRF_TOKEN = "input[name='csrf_token']"
SELECT_FORECAST_DAYS = "select[name='forecast_days']"

# =============================================================================
# Expected Text Content
# =============================================================================

# Page Titles
TITLE_HOME = "Weather Dashboard - Home"
TITLE_WEATHER_PREFIX = "Weather for"
TITLE_FORECAST_PREFIX = "Weather Forecast for"

# Headings
HEADING_WEATHER_DASHBOARD = "Weather Dashboard"
HEADING_WEATHER_FOR_PREFIX = "Weather for"
HEADING_FORECAST_FOR_PREFIX = "Forecast for"

# Card Titles
CARD_TITLE_ASK_WEATHER = "Ask About Weather"
CARD_TITLE_SEARCH_LOCATION = "Search Location"
CARD_TITLE_WEATHER_FORECAST = "Weather Forecast"
CARD_TITLE_FAVORITE_LOCATIONS = "Favorite Locations"
CARD_TITLE_POPULAR_CITIES = "Popular Cities"

# Button Text
BUTTON_SEARCH = "Search"
BUTTON_GET_FORECAST = "Get Forecast"
BUTTON_UPDATE_FORECAST = "Update Forecast"
BUTTON_ADD_TO_FAVORITES = "Add to Favorites"
BUTTON_REMOVE_FROM_FAVORITES = "Remove from Favorites"

# Link Text
LINK_BACK_TO_HOME = "Back to Home"
LINK_VIEW_FORECAST = "View Forecast"
LINK_CURRENT_WEATHER = "Current Weather"
LINK_SWITCH_TO_CELSIUS = "Switch to °C"
LINK_SWITCH_TO_FAHRENHEIT = "Switch to °F"

# Weather Detail Labels
LABEL_FEELS_LIKE = "Feels like:"
LABEL_HUMIDITY = "Humidity:"
LABEL_WIND = "Wind:"
LABEL_PRESSURE = "Pressure:"
LABEL_PRECIPITATION = "Precipitation:"
LABEL_UV_INDEX = "UV Index:"
LABEL_RAIN_CHANCE = "Rain Chance:"
LABEL_SNOW_CHANCE = "Snow Chance:"
LABEL_LAST_UPDATED = "Last updated:"
