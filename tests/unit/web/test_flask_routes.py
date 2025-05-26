"""Unit tests for Flask routes and app functionality."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using absolute path - fix the path calculation
web_app_path = project_root / "web" / "app.py"
spec = __import__("importlib.util").util.spec_from_file_location(
    "web_app", web_app_path
)
web_app_module = __import__("importlib.util").util.module_from_spec(spec)
spec.loader.exec_module(web_app_module)
app = web_app_module.app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
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
            mock_forecast_data = []
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
        """Test API weather endpoint with successful response."""
        mock_weather_data = {
            "current": {"temp_c": 15.0, "temp_f": 59.0, "humidity": 80}
        }

        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_location = MagicMock()
            mock_get_weather.return_value = (mock_weather_data, mock_location)

            response = client.get("/api/weather/51.5074/-0.1278")
            assert response.status_code == 200
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            assert "current" in data
            assert data["current"]["temp_c"] == 15.0

    def test_api_weather_error(self, client):
        """Test API weather endpoint with error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = ValueError("API Error")

            response = client.get("/api/weather/51.5074/-0.1278")
            assert response.status_code == 400
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            assert "error" in data


class TestUnitRoute:
    """Test the unit preference route."""

    def test_update_unit_celsius(self, client, mock_settings_repo):
        """Test updating unit preference to Celsius."""
        response = client.post("/unit", data={"unit": "C"})
        assert response.status_code == 302  # Redirect to index
        mock_settings_repo.update_temperature_unit.assert_called_once_with("celsius")

    def test_update_unit_fahrenheit(self, client, mock_settings_repo):
        """Test updating unit preference to Fahrenheit."""
        response = client.post("/unit", data={"unit": "F"})
        assert response.status_code == 302  # Redirect to index
        mock_settings_repo.update_temperature_unit.assert_called_once_with("fahrenheit")

    def test_update_unit_invalid(self, client, mock_settings_repo):
        """Test updating unit preference with invalid unit."""
        response = client.post("/unit", data={"unit": "X"})
        assert response.status_code == 302  # Redirect to index
        # Should not call update_temperature_unit with invalid unit
        mock_settings_repo.update_temperature_unit.assert_not_called()


class TestFavoriteRoute:
    """Test the favorite toggle route."""

    def test_toggle_favorite_success(self, client, mock_location_manager):
        """Test toggling favorite status successfully."""
        mock_location_manager.toggle_favorite.return_value = True

        response = client.post("/favorite/1")
        assert response.status_code == 302  # Redirect
        mock_location_manager.toggle_favorite.assert_called_once_with(1)

    def test_toggle_favorite_failure(self, client, mock_location_manager):
        """Test toggling favorite status with failure."""
        mock_location_manager.toggle_favorite.return_value = False

        response = client.post("/favorite/1")
        assert response.status_code == 302  # Redirect
        mock_location_manager.toggle_favorite.assert_called_once_with(1)

    def test_toggle_favorite_with_next_parameter(self, client, mock_location_manager):
        """Test toggling favorite with next parameter."""
        mock_location_manager.toggle_favorite.return_value = True

        response = client.post("/favorite/1?next=/weather/51.5074/-0.1278")
        assert response.status_code == 302  # Redirect


class TestNaturalLanguageRoute:
    """Test the natural language weather query route."""

    def test_nl_query_valid(self, client, mock_weather_api):
        """Test natural language query with valid input."""
        mock_weather_api.search_city.return_value = [
            {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278}
        ]

        with (
            patch("web.app.get_weather_data") as mock_get_weather,
            patch("web.app.get_forecast_data") as mock_get_forecast,
        ):
            mock_weather_data = {"current": {"temp_c": 15.0}}
            mock_location = MagicMock()
            mock_location.name = "London"
            mock_get_weather.return_value = (mock_weather_data, mock_location)
            mock_get_forecast.return_value = []

            response = client.post(
                "/nl-date-weather",
                data={"query": "What is the weather like in London today?"},
            )
            assert response.status_code == 200

    def test_nl_query_no_location(self, client):
        """Test natural language query without location."""
        response = client.post(
            "/nl-date-weather", data={"query": "What is the weather like today?"}
        )
        assert response.status_code == 302  # Redirect to index

    def test_nl_query_location_not_found(self, client, mock_weather_api):
        """Test natural language query with location not found."""
        mock_weather_api.search_city.return_value = []

        with patch("web.app.location_manager") as mock_manager:
            mock_manager.get_coordinates.return_value = None

            response = client.post(
                "/nl-date-weather",
                data={"query": "What is the weather like in NonexistentCity?"},
            )
            assert response.status_code == 302  # Redirect to index


class TestUILocationRoute:
    """Test the UI location route."""

    def test_ui_location_valid(self, client, mock_weather_api):
        """Test UI location with valid location."""
        mock_weather_api.search_city.return_value = [
            {"name": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522}
        ]

        response = client.post("/ui", data={"location": "Paris"})
        assert response.status_code == 302  # Redirect to weather page

    def test_ui_location_empty(self, client):
        """Test UI location with empty location."""
        response = client.post("/ui", data={"location": ""})
        assert response.status_code == 302  # Redirect to index

    def test_ui_location_not_found(self, client, mock_weather_api):
        """Test UI location with location not found."""
        mock_weather_api.search_city.return_value = []

        response = client.post("/ui", data={"location": "NonexistentCity"})
        assert response.status_code == 302  # Redirect to index


class TestForecastFormRoute:
    """Test the forecast form route."""

    def test_forecast_form_with_coordinates(self, client):
        """Test forecast form with coordinates."""
        response = client.post(
            "/forecast", data={"lat": "51.5074", "lon": "-0.1278", "forecast_days": "7"}
        )
        assert response.status_code == 302  # Redirect to forecast page

    def test_forecast_form_with_location(self, client, mock_weather_api):
        """Test forecast form with location name."""
        mock_weather_api.search_city.return_value = [
            {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503}
        ]

        response = client.post(
            "/forecast", data={"location": "Tokyo", "forecast_days": "5"}
        )
        assert response.status_code == 302  # Redirect to forecast page

    def test_forecast_form_no_location(self, client):
        """Test forecast form without location or coordinates."""
        response = client.post("/forecast", data={"forecast_days": "7"})
        assert response.status_code == 302  # Redirect to index


class TestForecastPathRoute:
    """Test the forecast path route."""

    def test_forecast_path_valid_coordinates(self, client):
        """Test forecast path with valid coordinates."""
        with patch("web.app.get_forecast_data") as mock_get_forecast:
            mock_get_forecast.return_value = []

            response = client.get("/forecast/51.5074/-0.1278")
            assert response.status_code == 200

    def test_forecast_path_invalid_coordinates(self, client):
        """Test forecast path with invalid coordinates."""
        response = client.get("/forecast/invalid/coords")
        assert response.status_code == 302  # Redirect to index


class TestErrorHandling:
    """Test error handling across routes."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

    def test_weather_route_connection_error(self, client):
        """Test weather route with connection error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = ConnectionError("Connection failed")

            response = client.get("/weather/51.5074/-0.1278")
            assert response.status_code == 302  # Redirect to index

    def test_api_weather_timeout_error(self, client):
        """Test API weather route with timeout error."""
        with patch("web.app.get_weather_data") as mock_get_weather:
            mock_get_weather.side_effect = TimeoutError("Request timeout")

            response = client.get("/api/weather/51.5074/-0.1278")
            assert response.status_code == 503  # Service unavailable

            data = json.loads(response.data)
            assert "error" in data
            assert "connection error" in data["error"].lower()


class TestHelperFunctions:
    """Test helper functions used in routes."""

    def test_get_weather_data_function(self, client):
        """Test the get_weather_data helper function."""
        with (
            patch("web.app.weather_api") as mock_api,
            patch("web.app.Helpers") as mock_helpers,
        ):
            mock_api.get_weather.return_value = {
                "current": {"temp_c": 15.0},
                "location": {"name": "London"},
            }

            mock_location = MagicMock()
            mock_helpers.get_location_by_coordinates.return_value = (
                mock_location,
                None,
            )
            mock_helpers.update_location_from_api_data.return_value = mock_location

            from web.app import get_weather_data

            result = get_weather_data((51.5074, -0.1278), "C")
            assert result is not None
            assert len(result) == 2  # Should return (weather_data, location)
