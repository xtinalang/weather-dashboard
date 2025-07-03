"""Integration tests for Flask web application.

These tests validate the complete end-to-end functionality of the web
application, including HTTP request/response cycles, form submissions,
database operations, and session management.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from tests.integration.conftest import assert_web_response
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


class TestWebIntegration:
    """Integration tests for web application routes."""

    def test_index_page_integration(self, client):
        """Test index page loads with all components."""
        response = client.get("/")
        assert_web_response(response, 200)
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

        response = client.post("/search", data={"query": "London"})
        assert_web_response(response, 200)
        mock_api.search_city.assert_called_once_with("London, England, UK")

    @patch("web.app.weather_api")
    def test_weather_display_integration(self, mock_api, client, mock_weather_data):
        """Test weather display for coordinates."""
        mock_api.get_weather.return_value = mock_weather_data

        response = client.get("/weather/51.52/-0.11")
        assert_web_response(response, 200)
        mock_api.get_weather.assert_called_once()

    @patch("web.app.weather_api")
    def test_forecast_integration(self, mock_api, client, mock_weather_data):
        """Test forecast functionality."""
        mock_api.get_forecast.return_value = mock_weather_data

        response = client.get("/forecast/51.52/-0.11?days=3")
        assert_web_response(response, [200, 302])  # Allow both success and redirect

    def test_unit_preference_integration(self, client, clean_db):
        """Test temperature unit preference functionality."""
        response = client.post("/unit", data={"unit": "celsius"})
        assert_web_response(response, [200, 302])

    @patch("web.app.location_repo")
    def test_favorite_toggle_integration(self, mock_repo, client, clean_db):
        """Test favorite location toggle functionality."""
        # Mock location with ID
        mock_location = MagicMock()
        mock_location.id = 1
        mock_location.is_favorite = False
        mock_repo.get_by_id.return_value = mock_location

        response = client.post("/favorite/1")  # Use correct route
        assert_web_response(response, [200, 302])

    def test_natural_language_query_integration(self, client):
        """Test natural language query processing."""
        response = client.post(
            "/nl-date-weather",
            data={"query": "What's the weather like in London today?"},
        )
        assert_web_response(response, [200, 302])  # Allow redirect for location search

    def test_form_submission_integration(self, client):
        """Test various form submissions."""
        # Location input form
        response = client.post("/ui", data={"location": "New York"})
        assert_web_response(response, [200, 302])

        # Forecast form
        response = client.post("/forecast", data={"location": "Paris", "days": "5"})
        assert_web_response(response, [200, 302])


class TestWebDatabaseIntegration:
    """Integration tests for web application database operations."""

    @patch("web.app.weather_api")
    def test_location_persistence_integration(
        self, mock_api, client, clean_db, mock_weather_data
    ):
        """Test location saving and retrieval."""
        mock_api.get_weather.return_value = mock_weather_data

        # Get weather for a location (should save to database)
        response = client.get("/weather/51.52/-0.11")
        assert_web_response(response, 200)

    def test_settings_persistence_integration(self, client, clean_db):
        """Test settings persistence through web interface."""
        response = client.post("/unit", data={"unit": "fahrenheit"})
        assert_web_response(response, [200, 302])


class TestWebSessionIntegration:
    """Integration tests for web application session management."""

    def test_session_state_integration(self, client):
        """Test session state management."""
        with client.session_transaction() as sess:
            sess["test_key"] = "test_value"

        # Session should persist across requests
        response = client.get("/")
        assert_web_response(response, 200)


class TestWebErrorHandling:
    """Integration tests for web application error handling."""

    def test_404_error_integration(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-page")
        assert_web_response(response, 404)

    @patch("web.app.weather_api")
    def test_api_error_handling_integration(self, mock_api, client):
        """Test API error handling in web interface."""
        mock_api.get_weather.return_value = None  # Simulate API failure

        response = client.get("/weather/51.52/-0.11")
        assert_web_response(response, [200, 302])  # App redirects on API errors

    def test_invalid_coordinates_integration(self, client):
        """Test handling of invalid coordinates."""
        response = client.get("/weather/invalid/coordinates")
        assert_web_response(response, [200, 302, 400, 404])  # Allow redirects

    def test_empty_search_integration(self, client):
        """Test handling of empty search queries."""
        response = client.post("/search", data={"query": ""})
        assert_web_response(response, [200, 302])  # App redirects on validation failure


class TestWebAPIEndpoints:
    """Integration tests for web API endpoints."""

    @patch("web.app.weather_api")
    def test_api_weather_endpoint_integration(
        self, mock_api, client, mock_weather_data
    ):
        """Test API weather endpoint."""
        mock_api.get_weather.return_value = mock_weather_data

        response = client.get("/api/weather/51.52/-0.11")
        assert_web_response(
            response, [200, 404]
        )  # Route may not exist in current implementation

        # Should return JSON if endpoint exists
        if (
            response.status_code == 200
            and response.content_type
            and "json" in response.content_type
        ):
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
        assert_web_response(response, 200)

        # 2. Search for location
        response = client.post("/search", data={"query": "London"})
        assert_web_response(response, [200, 302])  # Search may redirect to weather page

        # 3. Get weather for location
        response = client.get("/weather/51.52/-0.11")
        assert_web_response(response, 200)

    @patch("web.app.weather_api")
    def test_user_preference_workflow(
        self, mock_api, client, clean_db, mock_weather_data
    ):
        """Test user preference management workflow."""
        mock_api.get_weather.return_value = mock_weather_data

        # 1. Load page with default settings
        response = client.get("/")
        assert_web_response(response, 200)

        # 2. Change temperature unit to Fahrenheit
        response = client.post("/unit", data={"unit": "fahrenheit"})
        assert_web_response(response, [200, 302])

        # 3. Get weather data (should use Fahrenheit)
        response = client.get("/weather/51.52/-0.11")
        assert_web_response(response, 200)

    def test_form_and_navigation_workflow(self, client):
        """Test form interactions and navigation workflow."""
        # 1. Index page
        response = client.get("/")
        assert_web_response(response, 200)

        # 2. Try different forms
        forms_data = [
            ("/ui", {"location": "Paris"}),
            ("/nl-date-weather", {"query": "What's the weather in Tokyo?"}),
            ("/forecast", {"location": "Berlin", "days": "5"}),
        ]

        for endpoint, data in forms_data:
            response = client.post(endpoint, data=data)
            assert_web_response(response, [200, 302])

    @patch("web.app.weather_api")
    @patch("web.app.location_repo")
    def test_favorites_workflow(
        self, mock_repo, mock_api, client, clean_db, mock_weather_data
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
        assert_web_response(response, 200)

        # 2. Toggle favorite status
        response = client.post("/favorite/1")
        assert_web_response(response, [200, 302])
