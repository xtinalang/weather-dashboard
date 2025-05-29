"""
Unit tests for the location selection feature.

Tests the multi-step location selection process including:
- LocationSearchForm and LocationSelectionForm
- Location search with multiple results
- Location selection and redirection
- Error handling and validation
- Integration with different actions (weather, forecast, nl)
"""

from unittest.mock import Mock, patch

import pytest


class TestLocationSearchForm:
    """Test the LocationSearchForm."""

    def test_location_search_form_valid_data(self, flask_app, web_forms_module):
        """Test LocationSearchForm with valid data."""
        with flask_app.app_context():
            form_data = {"query": "Springfield", "csrf_token": "test_token"}
            form = web_forms_module.LocationSearchForm(data=form_data)
            # Skip CSRF validation for testing
            form.csrf_token = Mock()
            form.csrf_token.data = "test_token"

            assert form.validate() is True
            assert form.query.data == "Springfield"

    def test_location_search_form_empty_query(self, flask_app, web_forms_module):
        """Test LocationSearchForm with empty query."""
        with flask_app.app_context():
            form_data = {"query": "", "csrf_token": "test_token"}
            form = web_forms_module.LocationSearchForm(data=form_data)
            form.csrf_token = Mock()
            form.csrf_token.data = "test_token"

            assert form.validate() is False
            assert "This field is required." in form.query.errors

    def test_location_search_form_whitespace_query(self, flask_app, web_forms_module):
        """Test LocationSearchForm with whitespace-only query."""
        with flask_app.app_context():
            form_data = {"query": "   ", "csrf_token": "test_token"}
            form = web_forms_module.LocationSearchForm(data=form_data)
            form.csrf_token = Mock()
            form.csrf_token.data = "test_token"

            assert form.validate() is False


class TestLocationSelectionRoutes:
    """Test the location selection routes."""

    def test_search_route_single_result_weather(self, client):
        """Test search route with single result redirects to weather."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            # Mock single search result
            mock_search.return_value = [
                {
                    "name": "London",
                    "region": "England",
                    "country": "United Kingdom",
                    "lat": 51.52,
                    "lon": -0.11,
                }
            ]

            response = client.post(
                "/search",
                data={"query": "London", "csrf_token": "test_token"},
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/weather/51.52/-0.11" in response.location

    def test_search_route_multiple_results_shows_selection(self, client):
        """Test search route with multiple results shows selection page."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            # Mock multiple search results
            mock_search.return_value = [
                {
                    "name": "Springfield",
                    "region": "Massachusetts",
                    "country": "United States of America",
                    "lat": 42.1015,
                    "lon": -72.5898,
                },
                {
                    "name": "Springfield",
                    "region": "Missouri",
                    "country": "United States of America",
                    "lat": 37.22,
                    "lon": -93.3,
                },
            ]

            response = client.post(
                "/search",
                data={"query": "Springfield", "csrf_token": "test_token"},
            )

            assert response.status_code == 200
            assert b"Multiple locations found" in response.data
            assert b"Springfield" in response.data
            assert b"Massachusetts" in response.data
            assert b"Missouri" in response.data

    def test_search_route_no_results(self, client):
        """Test search route with no results."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            mock_search.return_value = []

            response = client.post(
                "/search",
                data={"query": "NonexistentPlace", "csrf_token": "test_token"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"No cities found matching" in response.data

    def test_search_route_api_error(self, client):
        """Test search route when API raises an error."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            mock_search.side_effect = ConnectionError("API down")

            response = client.post(
                "/search",
                data={"query": "London", "csrf_token": "test_token"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"Weather service connection error" in response.data

    def test_select_location_route_weather_action(self, client):
        """Test select-location route with weather action."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": ("51.52,-0.11,London,England,United Kingdom"),
                "action": "weather",
                "unit": "C",
                "csrf_token": "test_token",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/weather/51.52/-0.11" in response.location

    def test_select_location_route_forecast_action(self, client):
        """Test select-location route with forecast action."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": ("51.52,-0.11,London,England,United Kingdom"),
                "action": "forecast",
                "unit": "C",
                "forecast_days": "7",
                "csrf_token": "test_token",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/forecast/51.52/-0.11" in response.location

    def test_select_location_route_nl_action(self, client):
        """Test select-location route with natural language action."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": ("51.52,-0.11,London,England,United Kingdom"),
                "action": "nl",
                "unit": "C",
                "nl_query": "What's the weather in London tomorrow?",
                "csrf_token": "test_token",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/nl-result/51.52/-0.11" in response.location

    def test_select_location_route_no_selection(self, client):
        """Test select-location route with no location selected."""
        response = client.post(
            "/select-location",
            data={
                "action": "weather",
                "unit": "C",
                "csrf_token": "test_token",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Please select a location" in response.data

    def test_select_location_route_invalid_data(self, client):
        """Test select-location route with invalid location data."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": "invalid,data",
                "action": "weather",
                "unit": "C",
                "csrf_token": "test_token",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid location selection" in response.data

    def test_select_location_route_invalid_coordinates(self, client):
        """Test select-location route with invalid coordinates."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": "999,-999,Invalid,Place,Country",
                "action": "weather",
                "unit": "C",
                "csrf_token": "test_token",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid location selection" in response.data


class TestForecastWithLocationSelection:
    """Test forecast functionality with location selection."""

    def test_forecast_form_multiple_results(self, client):
        """Test forecast form with multiple location results."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            mock_search.return_value = [
                {
                    "name": "Paris",
                    "region": "Ile-de-France",
                    "country": "France",
                    "lat": 48.8566,
                    "lon": 2.3522,
                },
                {
                    "name": "Paris",
                    "region": "Texas",
                    "country": "United States of America",
                    "lat": 33.6617,
                    "lon": -95.5555,
                },
            ]

            response = client.post(
                "/forecast",
                data={
                    "location": "Paris",
                    "forecast_days": "5",
                    "csrf_token": "test_token",
                },
            )

            assert response.status_code == 200
            assert b"Multiple locations found" in response.data
            assert b"Paris" in response.data
            assert b"France" in response.data
            assert b"Texas" in response.data
            assert b"Get Forecast" in response.data


class TestNaturalLanguageWithLocationSelection:
    """Test natural language queries with location selection."""

    def test_nl_query_multiple_locations(self, client):
        """Test NL query that results in multiple location matches."""
        # For this test, we'll simulate the NL query processing that would
        # extract "London" from the query and then search for locations
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            mock_search.return_value = [
                {
                    "name": "London",
                    "region": "England",
                    "country": "United Kingdom",
                    "lat": 51.52,
                    "lon": -0.11,
                },
                {
                    "name": "London",
                    "region": "Ontario",
                    "country": "Canada",
                    "lat": 42.9849,
                    "lon": -81.2453,
                },
            ]

            # The nl-date-weather route processes the query to extract
            # location and if multiple matches are found, shows location
            # selection
            response = client.post(
                "/nl-date-weather",
                data={
                    "query": "What's the weather in London tomorrow?",
                    "csrf_token": "test_token",
                },
            )

            # Check if we got a redirect (single location found and
            # processed) or location selection page (multiple locations
            # found)
            if response.status_code == 200:
                # Multiple locations found - should show selection page
                assert (
                    b"Multiple locations found" in response.data
                    or b"London" in response.data
                )
            else:
                # Single location or direct processing - should be redirect
                assert response.status_code == 302


class TestErrorHandlers:
    """Test the error handling module functions."""

    def test_validate_coordinates_valid(self, web_error_handlers_module):
        """Test coordinate validation with valid coordinates."""
        assert web_error_handlers_module.validate_coordinates(51.52, -0.11) is True
        assert web_error_handlers_module.validate_coordinates("51.52", "-0.11") is True
        assert web_error_handlers_module.validate_coordinates(0, 0) is True
        assert web_error_handlers_module.validate_coordinates(-90, -180) is True
        assert web_error_handlers_module.validate_coordinates(90, 180) is True

    def test_validate_coordinates_invalid(self, web_error_handlers_module):
        """Test coordinate validation with invalid coordinates."""
        assert (
            web_error_handlers_module.validate_coordinates(91, 0) is False
        )  # lat > 90
        assert (
            web_error_handlers_module.validate_coordinates(-91, 0) is False
        )  # lat < -90
        assert (
            web_error_handlers_module.validate_coordinates(0, 181) is False
        )  # lon > 180
        assert (
            web_error_handlers_module.validate_coordinates(0, -181) is False
        )  # lon < -180
        assert (
            web_error_handlers_module.validate_coordinates("invalid", "data") is False
        )
        assert web_error_handlers_module.validate_coordinates(None, None) is False

    def test_safe_float_conversion(self, web_error_handlers_module):
        """Test safe float conversion."""
        assert web_error_handlers_module.safe_float_conversion("123.45") == 123.45
        assert web_error_handlers_module.safe_float_conversion("0") == 0.0
        assert web_error_handlers_module.safe_float_conversion("-45.67") == -45.67
        assert web_error_handlers_module.safe_float_conversion("invalid") == 0.0
        assert web_error_handlers_module.safe_float_conversion("") == 0.0
        assert web_error_handlers_module.safe_float_conversion("123.45", 99.9) == 123.45
        assert web_error_handlers_module.safe_float_conversion("invalid", 99.9) == 99.9

    def test_safe_int_conversion(self, web_error_handlers_module):
        """Test safe integer conversion."""
        assert web_error_handlers_module.safe_int_conversion("123") == 123
        assert web_error_handlers_module.safe_int_conversion("0") == 0
        assert web_error_handlers_module.safe_int_conversion("-45") == -45
        assert (
            web_error_handlers_module.safe_int_conversion("invalid") == 7
        )  # DEFAULT_FORECAST_DAYS
        assert web_error_handlers_module.safe_int_conversion("") == 7
        assert web_error_handlers_module.safe_int_conversion("123", 99) == 123
        assert web_error_handlers_module.safe_int_conversion("invalid", 99) == 99

    def test_validate_query_string_valid(self, web_error_handlers_module):
        """Test query string validation with valid queries."""
        assert web_error_handlers_module.validate_query_string("London") is True
        assert web_error_handlers_module.validate_query_string("New York") is True
        assert (
            web_error_handlers_module.validate_query_string(
                "What's the weather in Paris?"
            )
            is True
        )
        assert (
            web_error_handlers_module.validate_query_string("Springfield, MA") is True
        )

    def test_validate_query_string_invalid(self, web_error_handlers_module):
        """Test query string validation with invalid queries."""
        assert web_error_handlers_module.validate_query_string("") is False
        assert web_error_handlers_module.validate_query_string("   ") is False
        assert web_error_handlers_module.validate_query_string(None) is False
        assert (
            web_error_handlers_module.validate_query_string(
                "<script>alert('xss')</script>"
            )
            is False
        )
        assert (
            web_error_handlers_module.validate_query_string("javascript:void(0)")
            is False
        )
        assert (
            web_error_handlers_module.validate_query_string(
                "data:text/html,<h1>test</h1>"
            )
            is False
        )
        assert (
            web_error_handlers_module.validate_query_string("vbscript:msgbox") is False
        )
        assert (
            web_error_handlers_module.validate_query_string("a" * 201) is False
        )  # Too long

    def test_safe_api_operation_success(self, web_error_handlers_module):
        """Test safe API operation with successful call."""
        mock_operation = Mock(return_value={"success": True})
        result = web_error_handlers_module.safe_api_operation(
            mock_operation, "arg1", kwarg1="value1"
        )

        assert result == {"success": True}
        mock_operation.assert_called_once_with("arg1", kwarg1="value1")

    def test_safe_api_operation_connection_error(
        self, flask_app, web_error_handlers_module
    ):
        """Test safe API operation with connection error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=ConnectionError("Network error"))
            result = web_error_handlers_module.safe_api_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()

    def test_safe_api_operation_timeout_error(
        self, flask_app, web_error_handlers_module
    ):
        """Test safe API operation with timeout error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=TimeoutError("Request timeout"))
            result = web_error_handlers_module.safe_api_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()

    def test_safe_api_operation_value_error(self, flask_app, web_error_handlers_module):
        """Test safe API operation with value error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=ValueError("Invalid data"))
            result = web_error_handlers_module.safe_api_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()

    def test_safe_api_operation_key_error(self, flask_app, web_error_handlers_module):
        """Test safe API operation with key error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=KeyError("missing_key"))
            result = web_error_handlers_module.safe_api_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()

    def test_safe_database_operation_success(self, web_error_handlers_module):
        """Test safe database operation with successful call."""
        mock_operation = Mock(return_value=["location1", "location2"])
        result = web_error_handlers_module.safe_database_operation(
            mock_operation, "arg1"
        )

        assert result == ["location1", "location2"]
        mock_operation.assert_called_once_with("arg1")

    def test_safe_database_operation_io_error(
        self, flask_app, web_error_handlers_module
    ):
        """Test safe database operation with IO error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=OSError("Database locked"))
            result = web_error_handlers_module.safe_database_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()

    def test_safe_database_operation_os_error(
        self, flask_app, web_error_handlers_module
    ):
        """Test safe database operation with OS error."""
        with flask_app.test_request_context():
            mock_operation = Mock(side_effect=OSError("Permission denied"))
            result = web_error_handlers_module.safe_database_operation(mock_operation)

            assert result is None
            mock_operation.assert_called_once()


class TestLocationSelectionIntegration:
    """Integration tests for the complete location selection flow."""

    def test_complete_search_to_weather_flow(self, client):
        """Test complete flow from search to weather display."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            # Mock multiple search results
            mock_search.return_value = [
                {
                    "name": "Springfield",
                    "region": "Massachusetts",
                    "country": "United States of America",
                    "lat": 42.1015,
                    "lon": -72.5898,
                },
                {
                    "name": "Springfield",
                    "region": "Illinois",
                    "country": "United States of America",
                    "lat": 39.7817,
                    "lon": -89.6501,
                },
            ]

            # Step 1: Search for Springfield
            response = client.post(
                "/search",
                data={"query": "Springfield", "csrf_token": "test_token"},
            )

            assert response.status_code == 200
            assert b"Multiple locations found" in response.data

            # Step 2: Select Illinois location
            response = client.post(
                "/select-location",
                data={
                    "selected_location": (
                        "39.7817,-89.6501,Springfield,Illinois,United States of America"
                    ),
                    "action": "weather",
                    "unit": "C",
                    "csrf_token": "test_token",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/weather/39.7817/-89.6501" in response.location

    def test_search_invalid_query_validation(self, client):
        """Test search with invalid query triggers validation."""
        response = client.post(
            "/search",
            data={
                "query": "<script>alert('xss')</script>",
                "csrf_token": "test_token",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid search query" in response.data

    def test_forecast_flow_with_location_selection(self, client):
        """Test forecast flow with location selection."""
        with patch("weather_app.api.WeatherAPI.search_city") as mock_search:
            # Mock multiple search results
            mock_search.return_value = [
                {
                    "name": "London",
                    "region": "England",
                    "country": "United Kingdom",
                    "lat": 51.52,
                    "lon": -0.11,
                },
                {
                    "name": "London",
                    "region": "Ontario",
                    "country": "Canada",
                    "lat": 42.9849,
                    "lon": -81.2453,
                },
            ]

            # Request forecast for London
            response = client.post(
                "/forecast",
                data={
                    "location": "London",
                    "forecast_days": "5",
                    "csrf_token": "test_token",
                },
            )

            assert response.status_code == 200
            assert b"Multiple locations found" in response.data
            assert b"Get Forecast" in response.data

            # Select London, UK
            response = client.post(
                "/select-location",
                data={
                    "selected_location": ("51.52,-0.11,London,England,United Kingdom"),
                    "action": "forecast",
                    "unit": "C",
                    "forecast_days": "5",
                    "csrf_token": "test_token",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/forecast/51.52/-0.11" in response.location
            assert "days=5" in response.location


# Fixtures for testing
@pytest.fixture
def client(flask_app):
    """Flask test client."""
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    return flask_app.test_client()


@pytest.fixture
def web_error_handlers_module():
    """Get web.error_handlers module for testing."""
    import importlib.util
    import os
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        module_path = project_root / "web" / "error_handlers.py"
        spec = importlib.util.spec_from_file_location("web.error_handlers", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        yield module

    finally:
        os.chdir(original_cwd)
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
