"""Integration tests for Natural Language functionality in Flask web application.

These tests validate the complete end-to-end functionality of natural language
weather queries, including location extraction, date parsing, weather data
retrieval, and result display.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tests.integration.conftest import assert_web_response
from web.app import app as flask_app
from web.helpers import extract_location_from_query


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
def mock_location_search_results():
    """Mock location search results for testing."""
    return [
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


@pytest.fixture
def mock_weather_data():
    """Mock weather data for testing."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
        },
        "current": {
            "temp_c": 15.0,
            "temp_f": 59.0,
            "feelslike_c": 14.0,
            "feelslike_f": 57.2,
            "humidity": 65,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            },
            "wind_kph": 10.8,
            "wind_mph": 6.7,
            "wind_dir": "WSW",
            "pressure_mb": 1013.0,
            "precip_mm": 0.0,
            "uv": 4.0,
            "last_updated": "2024-01-01 12:00",
        },
    }


@pytest.fixture
def mock_forecast_data():
    """Mock forecast data for testing."""
    return {
        "forecast": {
            "forecastday": [
                {
                    "date": "2024-01-01",
                    "day": {
                        "maxtemp_c": 18.0,
                        "maxtemp_f": 64.4,
                        "mintemp_c": 8.0,
                        "mintemp_f": 46.4,
                        "condition": {
                            "text": "Sunny",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                        },
                        "daily_chance_of_rain": 0,
                        "daily_chance_of_snow": 0,
                        "maxwind_kph": 15.0,
                        "maxwind_mph": 9.3,
                        "avghumidity": 60,
                        "totalprecip_mm": 0.0,
                        "totalprecip_in": 0.0,
                        "uv": 5.0,
                    },
                },
                {
                    "date": "2024-01-02",
                    "day": {
                        "maxtemp_c": 16.0,
                        "maxtemp_f": 60.8,
                        "mintemp_c": 7.0,
                        "mintemp_f": 44.6,
                        "condition": {
                            "text": "Partly cloudy",
                            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                        },
                        "daily_chance_of_rain": 20,
                        "daily_chance_of_snow": 0,
                        "maxwind_kph": 12.0,
                        "maxwind_mph": 7.5,
                        "avghumidity": 65,
                        "totalprecip_mm": 0.0,
                        "totalprecip_in": 0.0,
                        "uv": 4.0,
                    },
                },
            ]
        }
    }


class TestNaturalLanguageLocationExtraction:
    """Test location extraction from natural language queries."""

    def test_location_extraction_weather_in_location(self):
        """Test extracting location from 'weather in LOCATION' pattern."""
        test_cases = [
            ("What's the weather in London?", "London"),
            ("Weather in New York today", "New York"),
            ("Show me weather in San Francisco", "San Francisco"),
            ("Tell me the weather in Los Angeles tomorrow", "Los Angeles"),
        ]

        for query, expected_location in test_cases:
            result = extract_location_from_query(query)
            assert (
                result == expected_location
            ), f"Query: '{query}' -> Expected: '{expected_location}', Got: '{result}'"

    def test_location_extraction_location_weather(self):
        """Test extracting location from 'LOCATION weather' pattern."""
        test_cases = [
            ("London weather", "London"),
            ("New York weather tomorrow", "New York"),
            ("Paris forecast", "Paris"),
            ("Tokyo temperature", "Tokyo"),
        ]

        for query, expected_location in test_cases:
            result = extract_location_from_query(query)
            assert (
                result == expected_location
            ), f"Query: '{query}' -> Expected: '{expected_location}', Got: '{result}'"

    def test_location_extraction_complex_queries(self):
        """Test extracting location from complex natural language queries."""
        test_cases = [
            ("Will it rain in Boston next Monday?", "Boston"),
            ("What's the forecast for Chicago this week?", "Chicago"),
            ("Is it sunny in Miami today?", "Miami"),
            ("How hot is it in Phoenix right now?", "Phoenix"),
        ]

        for query, expected_location in test_cases:
            result = extract_location_from_query(query)
            assert (
                result == expected_location
            ), f"Query: '{query}' -> Expected: '{expected_location}', Got: '{result}'"

    def test_location_extraction_invalid_queries(self):
        """Test handling of invalid queries that should not extract locations."""
        invalid_queries = [
            "What's the weather like today?",  # No location
            "How is the weather?",  # No location
            "Tell me the forecast",  # No location
            "",  # Empty query
            "   ",  # Whitespace only
        ]

        for query in invalid_queries:
            with pytest.raises(ValueError, match="No location pattern matched"):
                extract_location_from_query(query)


class TestNaturalLanguageQueryProcessing:
    """Test natural language query processing through the web interface."""

    @patch("web.app.weather_api")
    def test_nl_query_single_location_result(
        self, mock_api, client, mock_weather_data, mock_forecast_data
    ):
        """Test NL query with single location result."""
        # Setup mock to return single location
        mock_api.search_city.return_value = [
            {
                "name": "London",
                "region": "City of London, Greater London",
                "country": "United Kingdom",
                "lat": 51.52,
                "lon": -0.11,
            }
        ]
        mock_api.get_weather.return_value = mock_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London today?"}
        )

        # Should redirect to location selection even for single result in NL queries
        assert_web_response(response, [200, 302])
        mock_api.search_city.assert_called_once_with("London")

    @patch("web.app.weather_api")
    def test_nl_query_multiple_location_results(
        self, mock_api, client, mock_location_search_results
    ):
        """Test NL query with multiple location results."""
        mock_api.search_city.return_value = mock_location_search_results

        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London tomorrow?"}
        )

        assert_web_response(response, 200)
        assert b"London" in response.data
        assert b"United Kingdom" in response.data
        assert b"Canada" in response.data
        mock_api.search_city.assert_called_once_with("London")

    def test_nl_query_no_location_extracted(self, client):
        """Test NL query when no location can be extracted."""
        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather like today?"}
        )

        assert_web_response(response, 302)  # Should redirect to index
        # Should show error message via flash

    def test_nl_query_empty_query(self, client):
        """Test NL query with empty query."""
        response = client.post("/nl-date-weather", data={"query": ""})

        assert_web_response(response, 302)  # Should redirect to index

    @patch("web.app.weather_api")
    def test_nl_query_api_error(self, mock_api, client):
        """Test NL query when weather API fails."""
        mock_api.search_city.side_effect = ConnectionError("API unavailable")

        response = client.post(
            "/nl-date-weather", data={"query": "Weather in London today"}
        )

        assert_web_response(response, 302)  # Should redirect to index with error


class TestNaturalLanguageLocationSelection:
    """Test natural language location selection workflow."""

    @patch("web.app.weather_api")
    def test_nl_location_selection_form_submission(
        self, mock_api, client, mock_weather_data, mock_forecast_data
    ):
        """Test location selection form submission for NL queries."""
        mock_api.get_weather.return_value = mock_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        response = client.post(
            "/select-location",
            data={
                "selected_location": (
                    "51.52,-0.11,London,City of London, Greater London,United Kingdom"
                ),
                "action": "nl",
                "unit": "C",
                "nl_query": "What's the weather in London today?",
            },
        )

        assert_web_response(response, 302)  # Should redirect to NL result
        # Should redirect to nl_result_with_coords route

    def test_nl_location_selection_no_selection(self, client):
        """Test location selection with no location selected."""
        response = client.post(
            "/select-location",
            data={
                "action": "nl",
                "unit": "C",
                "nl_query": "What's the weather in London today?",
            },
        )

        assert_web_response(response, 302)  # Should redirect to index with error

    def test_nl_location_selection_invalid_data(self, client):
        """Test location selection with invalid location data."""
        response = client.post(
            "/select-location",
            data={
                "selected_location": "invalid_data",
                "action": "nl",
                "unit": "C",
                "nl_query": "What's the weather in London today?",
            },
        )

        assert_web_response(response, 302)  # Should redirect to index with error


class TestNaturalLanguageResults:
    """Test natural language results display."""

    @patch("web.app.weather_api")
    @patch("web.helpers.Helpers.get_date_range_for_query")
    @patch("web.helpers.Helpers.filter_forecast_by_dates")
    @patch("web.helpers.get_weather_data")
    @patch("web.helpers.get_forecast_data")
    @patch("web.app.safe_location_lookup")
    @patch("web.helpers.Helpers.save_weather_record")  # Mock the database save
    @patch("weather_app.api.WeatherAPI.get_weather")  # Mock the real API calls
    @patch("weather_app.api.WeatherAPI.get_forecast")  # Mock the real API calls
    def test_nl_result_with_coordinates(
        self,
        mock_api_forecast,
        mock_api_weather,
        mock_save_record,
        mock_safe_lookup,
        mock_get_forecast,
        mock_get_weather,
        mock_filter,
        mock_date_range,
        mock_api,
        client,
        mock_weather_data,
        mock_forecast_data,
    ):
        """Test NL result display with coordinates."""
        # Mock location validation to always succeed
        mock_safe_lookup.return_value = (True, "")

        # Mock database save to prevent MagicMock errors
        mock_save_record.return_value = None

        # Create properly structured weather data that matches template expectations
        template_weather_data = {
            "current": {
                "temp_c": 15.0,
                "temp_f": 59.0,
                "feelslike_c": 14.0,
                "feelslike_f": 57.2,
                "humidity": 65,
                "condition": {
                    "text": "Partly cloudy",
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                },
                "wind_kph": 10.8,
                "wind_mph": 6.7,
                "wind_dir": "WSW",
                "pressure_mb": 1013.0,
                "precip_mm": 0.0,
                "uv": 4.0,
                "last_updated": "2024-01-01 12:00",
            },
            "location": {
                "name": "London",
                "country": "United Kingdom",
                "region": "City of London, Greater London",
                "lat": 51.52,
                "lon": -0.11,
            },
        }

        # Mock the real API calls to return structured data
        mock_api_weather.return_value = template_weather_data
        mock_api_forecast.return_value = mock_forecast_data

        # Configure the main weather_api mock to return data when called on
        mock_api.get_weather.return_value = template_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        # Mock the location object with proper attributes
        mock_location = MagicMock()
        mock_location.name = "London"
        mock_location.country = "United Kingdom"
        mock_location.region = "City of London, Greater London"
        mock_location.id = 581

        # Mock the helper functions that get weather and forecast data
        mock_get_weather.return_value = (template_weather_data, mock_location)
        mock_get_forecast.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        # Mock date range processing
        today = datetime.now()
        mock_date_range.return_value = (today, today)
        mock_filter.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "C"},
        )

        assert_web_response(response, 200)
        # Check that we're getting real weather values, not MagicMock objects
        assert b"15.0" in response.data  # temperature in Celsius
        assert b"59.0" in response.data  # temperature in Fahrenheit
        assert b"Partly cloudy" in response.data  # condition
        assert b"65" in response.data  # humidity
        assert b"10.8" in response.data  # wind speed
        # Check that forecast values are also working
        assert b"18.0" in response.data  # forecast max temp
        assert b"8.0" in response.data  # forecast min temp

    @patch("web.app.weather_api")
    def test_nl_result_api_error(self, mock_api, client):
        """Test NL result when weather API fails."""
        mock_api.get_weather.side_effect = ConnectionError("API unavailable")

        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "C"},
        )

        assert_web_response(response, 302)  # Should redirect to index with error

    def test_nl_result_invalid_coordinates(self, client):
        """Test NL result with invalid coordinates."""
        response = client.get(
            "/nl-result/invalid/coordinates",
            query_string={"query": "What's the weather in London today?", "unit": "C"},
        )

        assert_web_response(response, 302)  # Should redirect to index with error

    @patch("web.app.weather_api")
    @patch("web.helpers.Helpers.get_date_range_for_query")
    @patch("web.helpers.Helpers.filter_forecast_by_dates")
    @patch("web.helpers.get_weather_data")
    @patch("web.helpers.get_forecast_data")
    @patch("web.app.safe_location_lookup")
    @patch("web.helpers.Helpers.save_weather_record")  # Mock the database save
    @patch("weather_app.api.WeatherAPI.get_weather")  # Mock the real API calls
    @patch("weather_app.api.WeatherAPI.get_forecast")  # Mock the real API calls
    def test_nl_result_different_units(
        self,
        mock_api_forecast,
        mock_api_weather,
        mock_save_record,
        mock_safe_lookup,
        mock_get_forecast,
        mock_get_weather,
        mock_filter,
        mock_date_range,
        mock_api,
        client,
        mock_weather_data,
        mock_forecast_data,
    ):
        """Test NL result with different temperature units."""
        # Mock location validation to always succeed
        mock_safe_lookup.return_value = (True, "")

        # Mock database save to prevent MagicMock errors
        mock_save_record.return_value = None

        # Create properly structured weather data that matches template expectations
        template_weather_data = {
            "current": {
                "temp_c": 15.0,
                "temp_f": 59.0,
                "feelslike_c": 14.0,
                "feelslike_f": 57.2,
                "humidity": 65,
                "condition": {
                    "text": "Partly cloudy",
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                },
                "wind_kph": 10.8,
                "wind_mph": 6.7,
                "wind_dir": "WSW",
                "pressure_mb": 1013.0,
                "precip_mm": 0.0,
                "uv": 4.0,
                "last_updated": "2024-01-01 12:00",
            },
            "location": {
                "name": "London",
                "country": "United Kingdom",
                "region": "City of London, Greater London",
                "lat": 51.52,
                "lon": -0.11,
            },
        }

        # Mock the real API calls to return structured data
        mock_api_weather.return_value = template_weather_data
        mock_api_forecast.return_value = mock_forecast_data

        # Configure the main weather_api mock to return data when callled on
        mock_api.get_weather.return_value = template_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        # Mock the location object with proper attributes
        mock_location = MagicMock()
        mock_location.name = "London"
        mock_location.country = "United Kingdom"
        mock_location.region = "City of London, Greater London"
        mock_location.id = 581

        # Mock the helper functions that get weather and forecast data
        mock_get_weather.return_value = (template_weather_data, mock_location)
        mock_get_forecast.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        # Mock date range processing
        today = datetime.now()
        mock_date_range.return_value = (today, today)
        mock_filter.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        # Test Celsius
        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "C"},
        )
        assert_web_response(response, 200)

        # Test Fahrenheit
        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "F"},
        )
        assert_web_response(response, 200)


class TestNaturalLanguageDateParsing:
    """Test natural language date parsing functionality."""

    def test_nl_query_with_today(self, client):
        """Test NL query with 'today' keyword."""
        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London today?"}
        )

        assert_web_response(response, [200, 302])

    def test_nl_query_with_tomorrow(self, client):
        """Test NL query with 'tomorrow' keyword."""
        response = client.post(
            "/nl-date-weather", data={"query": "Will it rain in New York tomorrow?"}
        )

        assert_web_response(response, [200, 302])

    def test_nl_query_with_weekday(self, client):
        """Test NL query with weekday."""
        response = client.post(
            "/nl-date-weather",
            data={"query": "What's the weather in Chicago on Monday?"},
        )

        assert_web_response(response, [200, 302])

    def test_nl_query_with_this_week(self, client):
        """Test NL query with 'this week'."""
        response = client.post(
            "/nl-date-weather",
            data={"query": "What's the forecast for Boston this week?"},
        )

        assert_web_response(response, [200, 302])


class TestNaturalLanguageEndToEnd:
    """End-to-end tests for natural language functionality."""

    @patch("web.app.weather_api")
    @patch("web.helpers.Helpers.get_date_range_for_query")
    @patch("web.helpers.Helpers.filter_forecast_by_dates")
    def test_complete_nl_workflow_single_location(
        self,
        mock_filter,
        mock_date_range,
        mock_api,
        client,
        mock_weather_data,
        mock_forecast_data,
    ):
        """Test complete NL workflow with single location result."""
        # Setup mocks
        mock_api.search_city.return_value = [
            {
                "name": "London",
                "region": "City of London, Greater London",
                "country": "United Kingdom",
                "lat": 51.52,
                "lon": -0.11,
            }
        ]
        mock_api.get_weather.return_value = mock_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        today = datetime.now()
        mock_date_range.return_value = (today, today)
        mock_filter.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
            }
        ]

        # 1. Submit NL query
        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London today?"}
        )
        assert_web_response(response, 200)
        assert b"London" in response.data

        # 2. Select location
        response = client.post(
            "/select-location",
            data={
                "selected_location": (
                    "51.52,-0.11,London,City of London, Greater London,United Kingdom"
                ),
                "action": "nl",
                "unit": "C",
                "nl_query": "What's the weather in London today?",
            },
        )
        assert_web_response(response, 302)

    @patch("web.app.weather_api")
    def test_complete_nl_workflow_multiple_locations(
        self, mock_api, client, mock_location_search_results
    ):
        """Test complete NL workflow with multiple location results."""
        mock_api.search_city.return_value = mock_location_search_results

        # 1. Submit NL query
        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London tomorrow?"}
        )

        assert_web_response(response, 200)
        assert b"London" in response.data
        assert b"United Kingdom" in response.data
        assert b"Canada" in response.data

    @patch("web.app.weather_api")
    def test_nl_error_handling_workflow(self, mock_api, client):
        """Test NL workflow error handling."""
        # Test API error
        mock_api.search_city.side_effect = ConnectionError("API error")

        response = client.post(
            "/nl-date-weather", data={"query": "What's the weather in London today?"}
        )

        assert_web_response(response, 302)  # Should redirect with error

    def test_nl_form_validation(self, client):
        """Test NL form validation."""
        # Test various invalid inputs
        invalid_queries = [
            "",  # Empty
            "   ",  # Whitespace only
            "What's the weather?",  # No location
        ]

        for query in invalid_queries:
            response = client.post("/nl-date-weather", data={"query": query})
            assert_web_response(response, 302)  # Should redirect with error


class TestNaturalLanguageIntegrationWithOtherFeatures:
    """Test NL integration with other app features."""

    @patch("web.app.weather_api")
    @patch("web.helpers.Helpers.get_date_range_for_query")
    @patch("web.helpers.Helpers.filter_forecast_by_dates")
    @patch("web.helpers.get_weather_data")
    @patch("web.helpers.get_forecast_data")
    @patch("web.app.safe_location_lookup")
    @patch("web.helpers.Helpers.save_weather_record")  # Mock the database save
    @patch("weather_app.api.WeatherAPI.get_weather")  # Mock the real API calls
    @patch("weather_app.api.WeatherAPI.get_forecast")  # Mock the real API calls
    def test_nl_with_unit_preferences(
        self,
        mock_api_forecast,
        mock_api_weather,
        mock_save_record,
        mock_safe_lookup,
        mock_get_forecast,
        mock_get_weather,
        mock_filter,
        mock_date_range,
        mock_api,
        client,
        mock_weather_data,
        mock_forecast_data,
    ):
        """Test NL functionality with different unit preferences."""
        # Mock location validation to always succeed
        mock_safe_lookup.return_value = (True, "")

        # Mock database save to prevent MagicMock errors
        mock_save_record.return_value = None

        # Create properly structured weather data that matches template expectations
        template_weather_data = {
            "current": {
                "temp_c": 15.0,
                "temp_f": 59.0,
                "feelslike_c": 14.0,
                "feelslike_f": 57.2,
                "humidity": 65,
                "condition": {
                    "text": "Partly cloudy",
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                },
                "wind_kph": 10.8,
                "wind_mph": 6.7,
                "wind_dir": "WSW",
                "pressure_mb": 1013.0,
                "precip_mm": 0.0,
                "uv": 4.0,
                "last_updated": "2024-01-01 12:00",
            },
            "location": {
                "name": "London",
                "country": "United Kingdom",
                "region": "City of London, Greater London",
                "lat": 51.52,
                "lon": -0.11,
            },
        }

        # Mock the real API calls to return structured data
        mock_api_weather.return_value = template_weather_data
        mock_api_forecast.return_value = mock_forecast_data

        # Configure the main weather_api mock to return data when called on
        mock_api.get_weather.return_value = template_weather_data
        mock_api.get_forecast.return_value = mock_forecast_data

        # Mock the location object with proper attributes
        mock_location = MagicMock()
        mock_location.name = "London"
        mock_location.country = "United Kingdom"
        mock_location.region = "City of London, Greater London"
        mock_location.id = 581

        # Mock the helper functions that get weather and forecast data
        mock_get_weather.return_value = (template_weather_data, mock_location)
        mock_get_forecast.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        # Mock date range processing
        today = datetime.now()
        mock_date_range.return_value = (today, today)
        mock_filter.return_value = [
            {
                "date": "2024-01-01",
                "max_temp": 18.0,
                "min_temp": 8.0,
                "condition": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "chance_of_rain": 0,
                "chance_of_snow": 0,
                "maxwind_kph": 15.0,
                "maxwind_mph": 9.3,
                "wind_speed": 15.0,
                "wind_unit": "km/h",
                "humidity": 60,
                "totalprecip_mm": 0.0,
                "totalprecip_in": 0.0,
                "avghumidity": 60,
                "uv": 5.0,
            }
        ]

        # Test with Celsius
        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "C"},
        )
        assert_web_response(response, 200)

        # Test with Fahrenheit
        response = client.get(
            "/nl-result/51.52/-0.11",
            query_string={"query": "What's the weather in London today?", "unit": "F"},
        )
        assert_web_response(response, 200)

    @patch("web.app.weather_api")
    @patch("web.app.location_repo")
    def test_nl_with_favorites(self, mock_repo, mock_api, client, mock_weather_data):
        """Test NL functionality interaction with favorites."""
        mock_api.get_weather.return_value = mock_weather_data

        # Mock favorite location
        mock_location = MagicMock()
        mock_location.id = 1
        mock_location.name = "London"
        mock_location.is_favorite = True
        mock_repo.get_favorites.return_value = [mock_location]

        # Load index page (should show favorites)
        response = client.get("/")
        assert_web_response(response, 200)

    def test_nl_accessibility_and_ui(self, client):
        """Test NL interface accessibility and UI elements."""
        # Load index page
        response = client.get("/")
        assert_web_response(response, 200)

        # Check for NL form elements
        assert b'name="query"' in response.data or b"DateWeatherNLForm" in str(
            response.data
        )
