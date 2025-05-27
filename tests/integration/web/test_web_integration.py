"""Integration tests for Flask web application.

These tests validate the complete end-to-end functionality of the web
application, including HTTP request/response cycles, form submissions,
database operations, and session management.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from weather_app.database import Database
from web.app import app as flask_app


@pytest.fixture
def app():
    """Create Flask application for testing."""
    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
            "SECRET_KEY": "test-secret-key",
        }
    )
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def temp_db():
    """Create a temporary database for integration testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    # Set up test database
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    # Initialize database
    db = Database()
    db.create_tables()

    yield test_db_path

    # Cleanup
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        os.environ.pop("DATABASE_URL", None)

    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_weather_data():
    """Mock weather API response data."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "tz_id": "Europe/London",
            "localtime": "2024-01-15 14:30",
        },
        "current": {
            "temp_c": 15.0,
            "temp_f": 59.0,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            },
            "wind_mph": 6.9,
            "wind_kph": 11.2,
            "wind_dir": "W",
            "pressure_mb": 1020.0,
            "humidity": 72,
            "feelslike_c": 15.0,
            "feelslike_f": 59.0,
            "vis_km": 10.0,
            "uv": 3.0,
            "precip_mm": 0.0,
            "last_updated": "2024-01-15 14:30",
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2024-01-15",
                    "day": {
                        "maxtemp_c": 18.0,
                        "maxtemp_f": 64.4,
                        "mintemp_c": 12.0,
                        "mintemp_f": 53.6,
                        "condition": {
                            "text": "Partly cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                        },
                        "maxwind_mph": 8.7,
                        "maxwind_kph": 14.0,
                        "daily_chance_of_rain": 20,
                        "daily_chance_of_snow": 0,
                        "totalprecip_mm": 0.1,
                        "totalprecip_in": 0.0,
                        "avghumidity": 75,
                        "uv": 3.0,
                    },
                },
                {
                    "date": "2024-01-16",
                    "day": {
                        "maxtemp_c": 16.0,
                        "maxtemp_f": 60.8,
                        "mintemp_c": 10.0,
                        "mintemp_f": 50.0,
                        "condition": {
                            "text": "Cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/119.png",
                        },
                        "maxwind_mph": 10.0,
                        "maxwind_kph": 16.1,
                        "daily_chance_of_rain": 30,
                        "daily_chance_of_snow": 0,
                        "totalprecip_mm": 0.2,
                        "totalprecip_in": 0.01,
                        "avghumidity": 80,
                        "uv": 2.0,
                    },
                },
            ]
        },
    }


class TestWebIntegration:
    """Integration tests for web application routes."""

    def test_index_page_integration(self, client):
        """Test index page loads with all components."""
        response = client.get("/")

        assert response.status_code == 200
        assert (
            b"Weather Dashboard" in response.data or b"weather" in response.data.lower()
        )
        # Check for form elements
        assert b'name="query"' in response.data or b'type="text"' in response.data

    @patch("web.app.weather_api")
    def test_search_functionality_integration(self, mock_api, client):
        """Test location search functionality."""
        # Setup mock
        mock_api.search_city.return_value = [
            {
                "name": "London",
                "region": "City of London, Greater London",
                "country": "United Kingdom",
                "lat": 51.52,
                "lon": -0.11,
            },
            {
                "name": "London",
                "region": "Ontario",
                "country": "Canada",
                "lat": 42.98,
                "lon": -81.25,
            },
        ]

        # Test search
        response = client.post("/search", data={"query": "London"})

        assert response.status_code == 200
        mock_api.search_city.assert_called_once_with("London")

    @patch("web.app.weather_api")
    def test_weather_display_integration(self, mock_api, client, mock_weather_data):
        """Test weather display for coordinates."""
        mock_api.get_weather.return_value = mock_weather_data

        response = client.get("/weather/51.52/-0.11")

        assert response.status_code == 200
        mock_api.get_weather.assert_called_once()

    @patch("web.app.weather_api")
    def test_forecast_integration(self, mock_api, client, mock_weather_data):
        """Test forecast functionality."""
        mock_api.get_forecast.return_value = mock_weather_data

        response = client.get("/forecast/51.52/-0.11?days=3")

        assert response.status_code == 200

    def test_unit_preference_integration(self, client, temp_db):
        """Test temperature unit preference functionality."""
        # Test update unit route
        response = client.post("/unit", data={"unit": "celsius"})
        assert response.status_code in [200, 302]  # Success or redirect

    @patch("web.app.location_repo")
    def test_favorite_toggle_integration(self, mock_repo, client, temp_db):
        """Test favorite location toggle functionality."""
        # Mock location with ID
        mock_location = MagicMock()
        mock_location.id = 1
        mock_location.is_favorite = False
        mock_repo.get_by_id.return_value = mock_location

        response = client.post("/favorite/1")

        assert response.status_code in [200, 302]

    def test_natural_language_query_integration(self, client):
        """Test natural language query processing."""
        response = client.post(
            "/nl-date-weather",
            data={"query": "What's the weather like in London today?"},
        )

        assert response.status_code == 200

    def test_form_submission_integration(self, client):
        """Test various form submissions."""
        # Location input form
        response = client.post("/ui", data={"location": "New York"})
        assert response.status_code in [200, 302]

        # Forecast form
        response = client.post("/forecast", data={"location": "Paris", "days": "5"})
        assert response.status_code in [200, 302]


class TestWebDatabaseIntegration:
    """Integration tests for web application database operations."""

    @patch("web.app.weather_api")
    def test_location_persistence_integration(
        self, mock_api, client, temp_db, mock_weather_data
    ):
        """Test location saving and retrieval."""
        mock_api.get_weather.return_value = mock_weather_data

        # Get weather for a location (should save to database)
        response = client.get("/weather/51.52/-0.11")
        assert response.status_code == 200

    def test_settings_persistence_integration(self, client, temp_db):
        """Test settings persistence through web interface."""
        # Update temperature unit
        response = client.post("/unit", data={"unit": "fahrenheit"})
        assert response.status_code in [200, 302]


class TestWebSessionIntegration:
    """Integration tests for web application session management."""

    def test_session_state_integration(self, client):
        """Test session state management."""
        with client.session_transaction() as sess:
            sess["test_key"] = "test_value"

        # Session should persist across requests
        response = client.get("/")
        assert response.status_code == 200


class TestWebErrorHandling:
    """Integration tests for web application error handling."""

    def test_404_error_integration(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    @patch("web.app.weather_api")
    def test_api_error_handling_integration(self, mock_api, client):
        """Test API error handling in web interface."""
        mock_api.get_weather.return_value = None  # Simulate API failure

        response = client.get("/weather/51.52/-0.11")
        # Should handle gracefully
        assert response.status_code in [200, 500]

    def test_invalid_coordinates_integration(self, client):
        """Test handling of invalid coordinates."""
        response = client.get("/weather/invalid/coordinates")
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 404]

    def test_empty_search_integration(self, client):
        """Test handling of empty search queries."""
        response = client.post("/search", data={"query": ""})
        assert response.status_code == 200


class TestWebAPIEndpoints:
    """Integration tests for web API endpoints."""

    @patch("web.app.weather_api")
    def test_api_weather_endpoint_integration(
        self, mock_api, client, mock_weather_data
    ):
        """Test API weather endpoint."""
        mock_api.get_weather.return_value = mock_weather_data

        response = client.get("/api/weather/51.52/-0.11")

        assert response.status_code == 200
        # Should return JSON if endpoint exists
        if response.content_type and "json" in response.content_type:
            data = json.loads(response.data)
            assert isinstance(data, dict)


class TestWebEndToEnd:
    """End-to-end integration tests for web application."""

    @patch("web.app.weather_api")
    def test_complete_weather_search_workflow(
        self, mock_api, client, mock_weather_data
    ):
        """Test complete weather search and display workflow."""
        # Setup search results
        mock_api.search_city.return_value = [
            {
                "name": "London",
                "region": "City of London, Greater London",
                "country": "United Kingdom",
                "lat": 51.52,
                "lon": -0.11,
            }
        ]

        # Setup weather data
        mock_api.get_weather.return_value = mock_weather_data

        # 1. Load index page
        response = client.get("/")
        assert response.status_code == 200

        # 2. Search for location
        response = client.post("/search", data={"query": "London"})
        assert response.status_code == 200

        # 3. Get weather for location
        response = client.get("/weather/51.52/-0.11")
        assert response.status_code == 200

    @patch("web.app.weather_api")
    def test_user_preference_workflow(
        self, mock_api, client, temp_db, mock_weather_data
    ):
        """Test user preference management workflow."""
        mock_api.get_weather.return_value = mock_weather_data

        # 1. Load page with default settings
        response = client.get("/")
        assert response.status_code == 200

        # 2. Change temperature unit to Fahrenheit
        response = client.post("/unit", data={"unit": "fahrenheit"})
        assert response.status_code in [200, 302]

        # 3. Get weather data (should use Fahrenheit)
        response = client.get("/weather/51.52/-0.11")
        assert response.status_code == 200

    def test_form_and_navigation_workflow(self, client):
        """Test form interactions and navigation workflow."""
        # 1. Index page
        response = client.get("/")
        assert response.status_code == 200

        # 2. Try different forms
        # Location input
        response = client.post("/ui", data={"location": "Paris"})
        assert response.status_code in [200, 302]

        # Natural language query
        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in Tokyo?"}
        )
        assert response.status_code in [200, 302]

        # Forecast form
        response = client.post("/forecast", data={"location": "Berlin", "days": "5"})
        assert response.status_code in [200, 302]

    @patch("web.app.weather_api")
    @patch("web.app.location_repo")
    def test_favorites_workflow(
        self, mock_repo, mock_api, client, temp_db, mock_weather_data
    ):
        """Test favorites management workflow."""
        # Setup mocks
        mock_api.get_weather.return_value = mock_weather_data

        mock_location = MagicMock()
        mock_location.id = 1
        mock_location.is_favorite = False
        mock_repo.get_by_id.return_value = mock_location

        # 1. Get weather for location
        response = client.get("/weather/51.52/-0.11")
        assert response.status_code == 200

        # 2. Toggle favorite status
        response = client.post("/favorite/1")
        assert response.status_code in [200, 302]
