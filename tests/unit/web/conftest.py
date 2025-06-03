"""
Configuration and fixtures for unit tests of the web interface.

This module provides fixtures for testing the Flask web application,
including app setup, request contexts, and mock data.
"""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# The imports below need to be after sys.path manipulation
# Add project root to path for imports


def setup_project_path():
    """Set up the project path for imports."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    original_cwd = os.getcwd()
    os.chdir(project_root)
    return project_root, original_cwd


@pytest.fixture(scope="session")
def project_setup():
    """Set up project path for the test session."""
    project_root, original_cwd = setup_project_path()
    yield project_root
    os.chdir(original_cwd)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))


@pytest.fixture
def flask_app(project_setup):
    """Create and configure a Flask app for testing."""
    # Import after path setup
    import web.app as web_app

    app = web_app.app
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        yield app


@pytest.fixture
def client(flask_app):
    """Create a test client."""
    return flask_app.test_client()


@pytest.fixture
def runner(flask_app):
    """Create a test CLI runner."""
    return flask_app.test_cli_runner()


@pytest.fixture
def mock_search():
    """Mock search function for testing."""
    mock = MagicMock()
    mock.return_value = [
        {
            "name": "London",
            "region": "England",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
        }
    ]
    return mock


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "tz_id": "Europe/London",
            "localtime_epoch": 1614556800,
            "localtime": "2021-03-01 12:00",
        },
        "current": {
            "last_updated_epoch": 1614556800,
            "last_updated": "2021-03-01 12:00",
            "temp_c": 15.0,
            "temp_f": 59.0,
            "is_day": 1,
            "condition": {"text": "Partly cloudy", "icon": "//example.com"},
            "wind_mph": 10.3,
            "wind_kph": 16.6,
            "wind_degree": 240,
            "wind_dir": "WSW",
            "pressure_mb": 1013.0,
            "pressure_in": 29.91,
            "precip_mm": 0.0,
            "precip_in": 0.0,
            "humidity": 65,
            "cloud": 25,
            "feelslike_c": 13.0,
            "feelslike_f": 55.4,
            "vis_km": 10.0,
            "vis_miles": 6.0,
            "uv": 3.0,
            "gust_mph": 15.6,
            "gust_kph": 25.1,
        },
    }


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing."""
    return {
        "location": {
            "name": "London",
            "region": "City of London, Greater London",
            "country": "United Kingdom",
            "lat": 51.52,
            "lon": -0.11,
            "tz_id": "Europe/London",
            "localtime_epoch": 1614556800,
            "localtime": "2021-03-01 12:00",
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2021-03-01",
                    "date_epoch": 1614556800,
                    "day": {
                        "maxtemp_c": 18.0,
                        "maxtemp_f": 64.4,
                        "mintemp_c": 8.0,
                        "mintemp_f": 46.4,
                        "avgtemp_c": 13.0,
                        "avgtemp_f": 55.4,
                        "maxwind_mph": 12.5,
                        "maxwind_kph": 20.2,
                        "totalprecip_mm": 2.5,
                        "totalprecip_in": 0.1,
                        "avgvis_km": 9.8,
                        "avgvis_miles": 6.1,
                        "avghumidity": 72.0,
                        "condition": {
                            "text": "Light rain",
                            "icon": "//example.com",
                        },
                        "uv": 3.0,
                    },
                    "astro": {
                        "sunrise": "06:45 AM",
                        "sunset": "05:58 PM",
                        "moonrise": "11:23 PM",
                        "moonset": "08:15 AM",
                        "moon_phase": "Waning Gibbous",
                        "moon_illumination": "72",
                    },
                }
            ]
        },
    }


@pytest.fixture
def web_forms_module(project_setup):
    """Get web.forms module for testing."""
    project_root = project_setup

    module_path = project_root / "web" / "forms.py"
    spec = importlib.util.spec_from_file_location("web.forms", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def web_utils_module(project_setup):
    """Get web.utils module for testing."""
    project_root = project_setup

    module_path = project_root / "web" / "utils.py"
    spec = importlib.util.spec_from_file_location("web.utils", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def web_modules_combined(project_setup):
    """Get both web.helpers and web.utils modules for testing."""
    # Use direct imports instead of importlib to ensure freezegun works properly
    import web.helpers as helpers_module
    import web.utils as utils_module

    return helpers_module, utils_module


# Mock objects for testing
@pytest.fixture
def mock_weather_api():
    """Mock WeatherAPI for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_location_manager():
    """Mock LocationManager for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_settings_repo():
    """Mock SettingsRepository for testing."""
    mock = MagicMock()
    return mock
