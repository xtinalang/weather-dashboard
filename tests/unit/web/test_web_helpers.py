"""Unit tests for web helpers and utilities."""

import importlib.util
import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest


def get_web_modules():
    """Dynamically load and return the web modules."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    # Add project root to path
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Load the web.helpers module dynamically
        helpers_path = project_root / "web" / "helpers.py"
        helpers_spec = importlib.util.spec_from_file_location(
            "web.helpers", helpers_path
        )
        web_helpers_module = importlib.util.module_from_spec(helpers_spec)
        helpers_spec.loader.exec_module(web_helpers_module)

        # Load the web.utils module dynamically
        utils_path = project_root / "web" / "utils.py"
        utils_spec = importlib.util.spec_from_file_location("web.utils", utils_path)
        web_utils_module = importlib.util.module_from_spec(utils_spec)
        utils_spec.loader.exec_module(web_utils_module)

        return web_helpers_module, web_utils_module, original_cwd, project_root

    except Exception:
        # Clean up on error
        os.chdir(original_cwd)
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
        raise


def cleanup_web_modules(original_cwd, project_root):
    """Clean up after using web modules."""
    os.chdir(original_cwd)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))


@pytest.fixture
def web_modules():
    """Get web modules for testing."""
    helpers_module, utils_module, original_cwd, project_root = get_web_modules()

    yield helpers_module, utils_module

    cleanup_web_modules(original_cwd, project_root)


class TestHelpers:
    """Test cases for Helpers class."""

    def test_parse_coordinates_from_path_valid(self, web_modules):
        """Test parsing valid coordinates from path."""
        web_helpers, _ = web_modules

        # Test positive coordinates
        lat, lon = web_helpers.Helpers.parse_coordinates_from_path("40.7128/-74.0060")
        assert lat == 40.7128
        assert lon == -74.0060

        # Test negative coordinates
        lat, lon = web_helpers.Helpers.parse_coordinates_from_path("-33.8688/151.2093")
        assert lat == -33.8688
        assert lon == 151.2093

    def test_parse_coordinates_from_path_invalid(self, web_modules):
        """Test parsing invalid coordinates from path."""
        web_helpers, _ = web_modules

        with pytest.raises(ValueError):
            web_helpers.Helpers.parse_coordinates_from_path("invalid/coords")

        with pytest.raises(ValueError):
            web_helpers.Helpers.parse_coordinates_from_path(
                "40.7128"
            )  # Missing longitude

        with pytest.raises(ValueError):
            web_helpers.Helpers.parse_coordinates_from_path(
                "40.7128/"
            )  # Empty longitude

    def test_get_normalized_unit_default(self, web_modules):
        """Test getting normalized unit with default value."""
        web_helpers, web_utils = web_modules

        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = None
            unit = web_helpers.Helpers.get_normalized_unit()
            assert unit == web_utils.DEFAULT_TEMP_UNIT

    def test_get_normalized_unit_celsius(self, web_modules):
        """Test getting normalized unit for Celsius."""
        web_helpers, _ = web_modules

        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "C"
            unit = web_helpers.Helpers.get_normalized_unit()
            assert unit == "C"

    def test_get_normalized_unit_fahrenheit(self, web_modules):
        """Test getting normalized unit for Fahrenheit."""
        web_helpers, _ = web_modules

        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "F"
            unit = web_helpers.Helpers.get_normalized_unit()
            assert unit == "F"

    def test_get_normalized_unit_lowercase(self, web_modules):
        """Test getting normalized unit with lowercase input."""
        web_helpers, _ = web_modules

        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "c"
            unit = web_helpers.Helpers.get_normalized_unit()
            assert unit == "C"

    def test_normalize_location_input_known_abbreviation(self, web_modules):
        """Test normalizing location input with known abbreviations."""
        web_helpers, _ = web_modules

        result = web_helpers.Helpers.normalize_location_input("UK")
        assert result == "United Kingdom"

        result = web_helpers.Helpers.normalize_location_input("USA")
        assert result == "United States"

        result = web_helpers.Helpers.normalize_location_input("UAE")
        assert result == "United Arab Emirates"

    def test_normalize_location_input_unknown_abbreviation(self, web_modules):
        """Test normalizing location input with unknown abbreviations."""
        web_helpers, _ = web_modules

        result = web_helpers.Helpers.normalize_location_input("Germany")
        assert result == "Germany"

        result = web_helpers.Helpers.normalize_location_input("XYZ")
        assert result == "XYZ"

    def test_get_date_range_for_query_tomorrow(self, web_modules):
        """Test getting date range for 'tomorrow' query."""
        web_helpers, _ = web_modules

        with patch("web.helpers.date") as mock_date:
            mock_today = date(2025, 5, 23)
            mock_date.today.return_value = mock_today

            dates = web_helpers.Helpers.get_date_range_for_query("tomorrow")
            expected = [date(2025, 5, 24)]
            assert dates == expected

    def test_get_date_range_for_query_this_weekend(self, web_modules):
        """Test getting date range for 'this weekend' query."""
        web_helpers, _ = web_modules

        with patch("web.helpers.date") as mock_date:
            # Mock a Friday (weekday 4)
            mock_today = date(2025, 5, 23)  # This is a Friday
            mock_date.today.return_value = mock_today

            dates = web_helpers.Helpers.get_date_range_for_query("this weekend")
            # Should return Saturday and Sunday
            expected = [date(2025, 5, 24), date(2025, 5, 25)]
            assert dates == expected

    def test_get_date_range_for_query_specific_weekday(self, web_modules):
        """Test getting date range for specific weekday."""
        web_helpers, _ = web_modules

        with patch("web.helpers.date") as mock_date:
            # Mock a Friday (weekday 4)
            mock_today = date(2025, 5, 23)
            mock_date.today.return_value = mock_today

            # Test Monday (should be next week)
            dates = web_helpers.Helpers.get_date_range_for_query("monday")
            expected = [date(2025, 5, 26)]  # Next Monday
            assert dates == expected

    def test_get_date_range_for_query_invalid(self, web_modules):
        """Test getting date range for invalid query."""
        web_helpers, _ = web_modules

        dates = web_helpers.Helpers.get_date_range_for_query("invalid query")
        assert dates == []


class TestConstants:
    """Test cases for web constants."""

    def test_location_abbreviation_mapping(self, web_modules):
        """Test location abbreviation mapping constant."""
        web_helpers, _ = web_modules

        assert isinstance(web_helpers.LOCATION_ABBREVIATION_MAPPING, dict)
        assert "UK" in web_helpers.LOCATION_ABBREVIATION_MAPPING
        assert "USA" in web_helpers.LOCATION_ABBREVIATION_MAPPING
        assert "UAE" in web_helpers.LOCATION_ABBREVIATION_MAPPING

    def test_weekday_names(self, web_modules):
        """Test weekday names constant."""
        web_helpers, _ = web_modules

        assert isinstance(web_helpers.WEEKDAY_NAMES, list)
        assert len(web_helpers.WEEKDAY_NAMES) == 7
        assert "monday" in web_helpers.WEEKDAY_NAMES
        assert "sunday" in web_helpers.WEEKDAY_NAMES

    def test_weekday_to_number(self, web_modules):
        """Test weekday to number mapping."""
        web_helpers, _ = web_modules

        assert isinstance(web_helpers.WEEKDAY_TO_NUMBER, dict)
        assert len(web_helpers.WEEKDAY_TO_NUMBER) == 7
        assert web_helpers.WEEKDAY_TO_NUMBER["monday"] == 0
        assert web_helpers.WEEKDAY_TO_NUMBER["sunday"] == 6

    def test_utils_constants(self, web_modules):
        """Test utility constants."""
        _, web_utils = web_modules

        assert web_utils.DEFAULT_TEMP_UNIT in ["C", "F"]
        assert isinstance(web_utils.VALID_TEMP_UNITS, (list, tuple))
        assert isinstance(web_utils.TEMPERATURE_UNIT_CHOICES, (list, tuple))
        assert isinstance(web_utils.FORECAST_DAYS_CHOICES, (list, tuple))

    def test_temperature_unit_choices_format(self, web_modules):
        """Test temperature unit choices format."""
        _, web_utils = web_modules

        for choice in web_utils.TEMPERATURE_UNIT_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert choice[0] in ["C", "F"]

    def test_forecast_days_choices_format(self, web_modules):
        """Test forecast days choices format."""
        _, web_utils = web_modules

        for choice in web_utils.FORECAST_DAYS_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert isinstance(choice[0], int)
            assert choice[0] > 0
