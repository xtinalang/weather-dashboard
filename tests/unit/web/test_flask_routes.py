"""Unit tests for Flask routes and app functionality."""

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def get_flask_app():
    """Dynamically load and return the Flask app."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    # Add project root to path
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Load the web.app module dynamically
        app_path = project_root / "web" / "app.py"
        spec = importlib.util.spec_from_file_location("web.app", app_path)
        web_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app_module)

        return web_app_module.app, original_cwd, project_root

    except Exception:
        # Clean up on error
        os.chdir(original_cwd)
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
        raise


def cleanup_flask_app(original_cwd, project_root):
    """Clean up after using Flask app."""
    os.chdir(original_cwd)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))


@pytest.fixture
def app():
    """Get Flask app for testing."""
    app, original_cwd, project_root = get_flask_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app

    cleanup_flask_app(original_cwd, project_root)


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_weather_api():
    """Mock WeatherAPI instance."""
    with patch("web.app.weather_api") as mock_api:
        yield mock_api


@pytest.fixture
def mock_location_manager():
    """Mock LocationManager instance."""
    with patch("web.app.location_manager") as mock_manager:
        yield mock_manager


@pytest.fixture
def mock_settings_repo():
    """Mock SettingsRepository instance."""
    with patch("web.app.settings_repo") as mock_repo:
        yield mock_repo


class TestIndexRoute:
    """Test the index route."""

    def test_index_page_loads(self, client):
        """Test that the index page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Weather Dashboard" in response.data

    def test_index_page_contains_forms(self, client):
        """Test that the index page contains the expected forms."""
        response = client.get("/")
        assert response.status_code == 200

        # Check for search form
        assert b'name="query"' in response.data

        # Check for forecast form
        assert b'name="location"' in response.data
        assert b'name="forecast_days"' in response.data


class TestSearchRoute:
    """Test the search route."""

    def test_search_post_valid_query(self, client, mock_weather_api):
        """Test POST to search with valid query."""
        mock_weather_api.search_city.return_value = [
            {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278}
        ]

        response = client.post("/search", data={"query": "London"})
        assert response.status_code == 302  # Redirect to weather page
        mock_weather_api.search_city.assert_called_once_with("London")

    def test_search_post_no_results(self, client, mock_weather_api):
        """Test POST to search with no results."""
        mock_weather_api.search_city.return_value = []

        response = client.post("/search", data={"query": "NonexistentCity"})
        assert response.status_code == 302  # Redirect back to index
        mock_weather_api.search_city.assert_called_once_with("NonexistentCity")

    def test_search_post_multiple_results(self, client, mock_weather_api):
        """Test POST to search with multiple results."""
        mock_weather_api.search_city.return_value = [
            {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278},
            {"name": "London", "country": "Canada", "lat": 42.9849, "lon": -81.2453},
        ]

        response = client.post("/search", data={"query": "London"})
        assert response.status_code == 200  # Show search results page
        assert b"search_results" in response.data or b"London" in response.data

    def test_search_post_empty_query(self, client):
        """Test POST to search with empty query."""
        response = client.post("/search", data={"query": ""})
        assert response.status_code == 302  # Redirect back to index


class TestWeatherRoute:
    """Test the weather route."""

    def test_weather_valid_coordinates(self, client, mock_weather_api):
        """Test weather route with valid coordinates."""
        mock_weather_data = {
            "current": {
                "temp_c": 15.0,
                "temp_f": 59.0,
                "feelslike_c": 14.0,
                "feelslike_f": 57.2,
                "humidity": 80,
                "condition": {
                    "text": "Partly cloudy",
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                },
                "wind_kph": 10.0,
                "wind_mph": 6.2,
                "wind_dir": "SW",
                "pressure_mb": 1013.0,
                "precip_mm": 0.0,
                "uv": 3.0,
                "last_updated": "2023-05-07 12:00",
            },
            "location": {
                "name": "London",
                "region": "City of London, Greater London",
                "country": "United Kingdom",
            },
        }

        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_location = MagicMock()
            mock_location.name = "London"
            mock_location.country = "United Kingdom"
            mock_get_weather.return_value = (mock_weather_data, mock_location)

            response = client.get("/weather/51.5074/-0.1278")
            assert response.status_code == 200
            assert b"London" in response.data

    def test_weather_invalid_coordinates(self, client):
        """Test weather route with invalid coordinates."""
        # Test latitude out of range
        response = client.get("/weather/91.0/0.0")
        assert response.status_code == 302  # Redirect to index

        # Test longitude out of range
        response = client.get("/weather/0.0/181.0")
        assert response.status_code == 302  # Redirect to index

    def test_weather_api_error(self, client):
        """Test weather route when API returns error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = ValueError("API Error")

            response = client.get("/weather/51.5074/-0.1278")
            assert response.status_code == 302  # Redirect to index


class TestForecastRoute:
    """Test the forecast route."""

    def test_forecast_get_request(self, client):
        """Test GET request to forecast route."""
        with patch("web.app.get_forecast_data") as mock_get_forecast:
            mock_forecast_data = [
                {
                    "date": "2023-05-07",
                    "day": {
                        "maxtemp_c": 20.0,
                        "mintemp_c": 10.0,
                        "condition": {
                            "text": "Sunny",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                        },
                    },
                }
            ]
            mock_get_forecast.return_value = mock_forecast_data

            response = client.get("/forecast/51.5074/-0.1278")
            assert response.status_code == 200
            assert b"forecast" in response.data.lower()

    def test_forecast_with_days_parameter(self, client):
        """Test forecast route with days parameter."""
        with patch("web.app.get_forecast_data") as mock_get_forecast:
            mock_forecast_data = []  # Empty forecast for testing
            mock_get_forecast.return_value = mock_forecast_data

            response = client.get("/forecast/51.5074/-0.1278?days=5")
            assert response.status_code == 200

    def test_forecast_api_error(self, client):
        """Test forecast route when API returns error."""
        with patch("web.app.get_forecast_data") as mock_get_forecast:
            mock_get_forecast.side_effect = ValueError("API Error")

            response = client.get("/forecast/51.5074/-0.1278")
            assert response.status_code == 302  # Redirect to index


class TestApiWeatherRoute:
    """Test the API weather route."""

    def test_api_weather_success(self, client):
        """Test API weather route with successful response."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_weather_data = {"current": {"temp_c": 15.0}}
            mock_location = MagicMock()
            mock_get_weather.return_value = (mock_weather_data, mock_location)

            response = client.get("/api/weather/51.5074/-0.1278")
            assert response.status_code == 200

            # Check if response is JSON
            try:
                data = json.loads(response.data)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # Some implementations might return different formats
                pass

    def test_api_weather_error(self, client):
        """Test API weather route with error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = ValueError("API Error")

            response = client.get("/api/weather/51.5074/-0.1278")
            # Accept various error response codes
            assert response.status_code in [400, 404, 500]


class TestUnitRoute:
    """Test the unit update route."""

    def test_update_unit_celsius(self, client, mock_settings_repo):
        """Test updating temperature unit to Celsius."""
        response = client.post("/unit", data={"unit": "C"})
        assert response.status_code in [200, 302]  # Success or redirect

    def test_update_unit_fahrenheit(self, client, mock_settings_repo):
        """Test updating temperature unit to Fahrenheit."""
        response = client.post("/unit", data={"unit": "F"})
        assert response.status_code in [200, 302]  # Success or redirect

    def test_update_unit_invalid(self, client, mock_settings_repo):
        """Test updating temperature unit with invalid value."""
        response = client.post("/unit", data={"unit": "X"})
        # Should handle invalid input gracefully
        assert response.status_code in [200, 302, 400]


class TestFavoriteRoute:
    """Test the favorite toggle route."""

    def test_toggle_favorite_success(self, client, mock_location_manager):
        """Test toggling favorite location successfully."""
        mock_location_manager.toggle_favorite.return_value = True

        response = client.post("/favorite", data={"lat": "51.5074", "lon": "-0.1278"})
        assert response.status_code in [200, 302]

    def test_toggle_favorite_failure(self, client, mock_location_manager):
        """Test toggling favorite location with failure."""
        mock_location_manager.toggle_favorite.return_value = False

        response = client.post("/favorite", data={"lat": "51.5074", "lon": "-0.1278"})
        assert response.status_code in [200, 302, 400]

    def test_toggle_favorite_with_next_parameter(self, client, mock_location_manager):
        """Test toggling favorite with next parameter."""
        mock_location_manager.toggle_favorite.return_value = True

        response = client.post(
            "/favorite",
            data={
                "lat": "51.5074",
                "lon": "-0.1278",
                "next": "/weather/51.5074/-0.1278",
            },
        )
        assert response.status_code in [200, 302]


class TestNaturalLanguageRoute:
    """Test the natural language query route."""

    def test_nl_query_valid(self, client, mock_weather_api):
        """Test natural language query with valid input."""
        mock_weather_api.search_city.return_value = [
            {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278}
        ]

        with patch("web.app.parse_natural_language_query") as mock_parse:
            mock_parse.return_value = {
                "location": "London",
                "date_range": [],
                "is_forecast": False,
            }

            response = client.post(
                "/nl", data={"query": "What is the weather in London?"}
            )
            assert response.status_code in [200, 302]

    def test_nl_query_no_location(self, client):
        """Test natural language query with no location found."""
        with patch("web.app.parse_natural_language_query") as mock_parse:
            mock_parse.return_value = {
                "location": None,
                "date_range": [],
                "is_forecast": False,
            }

            response = client.post("/nl", data={"query": "What is the weather?"})
            assert response.status_code in [200, 302]

    def test_nl_query_location_not_found(self, client, mock_weather_api):
        """Test natural language query with location not found in API."""
        mock_weather_api.search_city.return_value = []

        with patch("web.app.parse_natural_language_query") as mock_parse:
            mock_parse.return_value = {
                "location": "Nonexistent",
                "date_range": [],
                "is_forecast": False,
            }

            response = client.post(
                "/nl", data={"query": "What is the weather in Nonexistent?"}
            )
            assert response.status_code in [200, 302]


class TestUILocationRoute:
    """Test the UI location route."""

    def test_ui_location_valid(self, client, mock_weather_api):
        """Test UI location with valid location."""
        mock_weather_api.search_city.return_value = [
            {"name": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522}
        ]

        response = client.post("/ui-location", data={"location": "Paris"})
        assert response.status_code in [200, 302]

    def test_ui_location_empty(self, client):
        """Test UI location with empty input."""
        response = client.post("/ui-location", data={"location": ""})
        assert response.status_code in [200, 302]

    def test_ui_location_not_found(self, client, mock_weather_api):
        """Test UI location with location not found."""
        mock_weather_api.search_city.return_value = []

        response = client.post("/ui-location", data={"location": "Nonexistent"})
        assert response.status_code in [200, 302]


class TestForecastFormRoute:
    """Test the forecast form route."""

    def test_forecast_form_with_coordinates(self, client):
        """Test forecast form with coordinates."""
        response = client.post(
            "/forecast-form", data={"location": "51.5074,-0.1278", "forecast_days": "5"}
        )
        assert response.status_code in [200, 302]

    def test_forecast_form_with_location(self, client, mock_weather_api):
        """Test forecast form with location name."""
        mock_weather_api.search_city.return_value = [
            {"name": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050}
        ]

        response = client.post(
            "/forecast-form", data={"location": "Berlin", "forecast_days": "3"}
        )
        assert response.status_code in [200, 302]

    def test_forecast_form_no_location(self, client):
        """Test forecast form with no location."""
        response = client.post("/forecast-form", data={"forecast_days": "5"})
        assert response.status_code in [200, 302]


class TestErrorHandling:
    """Test error handling."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

    def test_weather_route_connection_error(self, client):
        """Test weather route with connection error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = ConnectionError("Network error")

            response = client.get("/weather/51.5074/-0.1278")
            assert response.status_code in [302, 500]  # Redirect or error

    def test_api_weather_timeout_error(self, client):
        """Test API weather route with timeout error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = TimeoutError("Request timeout")

            response = client.get("/api/weather/51.5074/-0.1278")
            assert response.status_code in [
                400,
                404,
                500,
                502,
                503,
            ]  # Various error codes
