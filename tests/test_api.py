"""Tests for the WeatherAPI class."""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from weather_app.api import WeatherAPI


@pytest.fixture
def mock_requests():
    """Mock the requests library."""
    with patch("weather_app.api.requests") as mock_req:
        yield mock_req


@pytest.fixture
def api_key():
    """Provide a test API key."""
    return "test_api_key"


@pytest.fixture
def api(api_key):
    """Create a WeatherAPI instance with a test API key."""
    with patch.dict(os.environ, {"WEATHER_API_KEY": api_key}):
        return WeatherAPI(api_key=api_key)


def test_init_with_api_key():
    """Test initialization with API key parameter."""
    api = WeatherAPI(api_key="test_key")
    assert api.api_key == "test_key"


def test_init_from_env():
    """Test initialization with API key from environment."""
    with patch.dict(os.environ, {"WEATHER_API_KEY": "env_key"}):
        with patch("weather_app.api.config") as mock_config:
            mock_config.return_value = "env_key"
            api = WeatherAPI()
            assert api.api_key == "env_key"


def test_init_no_api_key():
    """Test initialization with no API key raises an error."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("weather_app.api.config") as mock_config:
            mock_config.side_effect = KeyError("WEATHER_API_KEY")
            with pytest.raises(ValueError):
                WeatherAPI()


def test_get_weather_success(api, mock_requests):
    """Test successful weather retrieval."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "location": {"name": "London"},
        "current": {"temp_c": 15},
        "forecast": {"forecastday": [{"date": "2023-05-07"}]},
    }
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Call the method
    result = api.get_weather("London")

    # Check the result
    assert result is not None
    assert result["location"]["name"] == "London"
    assert result["current"]["temp_c"] == 15

    # Check that the API was called correctly
    mock_requests.get.assert_called_once()
    args, kwargs = mock_requests.get.call_args
    assert "forecast.json" in args[0]
    assert kwargs["params"]["q"] == "London"
    assert kwargs["params"]["key"] == api.api_key


def test_get_weather_request_exception(api, mock_requests):
    """Test weather retrieval with request exception."""
    # Mock request exception
    mock_requests.get.side_effect = requests.exceptions.RequestException(
        "Connection error"
    )

    # Call the method
    result = api.get_weather("London")

    # Check the result
    assert result is None

    # Check that the API was called
    mock_requests.get.assert_called_once()


def test_get_weather_other_exception(api, mock_requests):
    """Test weather retrieval with other exception."""
    # Mock other exception
    mock_requests.get.side_effect = Exception("Unexpected error")

    # Call the method
    result = api.get_weather("London")

    # Check the result
    assert result is None

    # Check that the API was called
    mock_requests.get.assert_called_once()


def test_search_city_success(api, mock_requests):
    """Test successful city search."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"name": "London", "country": "UK", "lat": 51.52, "lon": -0.11}
    ]
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Call the method
    result = api.search_city("London")

    # Check the result
    assert result is not None
    assert len(result) == 1
    assert result[0]["name"] == "London"

    # Check that the API was called correctly
    mock_requests.get.assert_called_once()
    args, kwargs = mock_requests.get.call_args
    assert "search.json" in args[0]
    assert kwargs["params"]["q"] == "London"
    assert kwargs["params"]["key"] == api.api_key


def test_search_city_no_results(api, mock_requests):
    """Test city search with no results."""
    # Mock empty response
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Call the method
    result = api.search_city("NonexistentCity")

    # Check the result
    assert result == []

    # Check that the API was called
    mock_requests.get.assert_called_once()


def test_search_city_request_exception(api, mock_requests):
    """Test city search with request exception."""
    # Mock request exception
    mock_requests.get.side_effect = requests.exceptions.RequestException(
        "Connection error"
    )

    # Call the method
    result = api.search_city("London")

    # Check the result
    assert result is None

    # Check that the API was called
    mock_requests.get.assert_called_once()


def test_search_city_other_exception(api, mock_requests):
    """Test city search with other exception."""
    # Mock other exception
    mock_requests.get.side_effect = Exception("Unexpected error")

    # Call the method
    result = api.search_city("London")

    # Check the result
    assert result is None

    # Check that the API was called
    mock_requests.get.assert_called_once()
