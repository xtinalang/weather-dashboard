"""Unit tests for web helpers and utilities."""

from datetime import date
from unittest.mock import patch

import pytest

from web.helpers import (
    LOCATION_ABBREVIATION_MAPPING,
    WEEKDAY_NAMES,
    WEEKDAY_TO_NUMBER,
    Helpers,
)
from web.utils import (
    DEFAULT_TEMP_UNIT,
    FORECAST_DAYS_CHOICES,
    TEMPERATURE_UNIT_CHOICES,
    VALID_TEMP_UNITS,
)


class TestHelpers:
    """Test cases for Helpers class."""

    def test_parse_coordinates_from_path_valid(self):
        """Test parsing valid coordinates from path."""
        # Test positive coordinates
        lat, lon = Helpers.parse_coordinates_from_path("40.7128/-74.0060")
        assert lat == 40.7128
        assert lon == -74.0060

        # Test negative coordinates
        lat, lon = Helpers.parse_coordinates_from_path("-33.8688/151.2093")
        assert lat == -33.8688
        assert lon == 151.2093

    def test_parse_coordinates_from_path_invalid(self):
        """Test parsing invalid coordinates from path."""
        with pytest.raises(ValueError):
            Helpers.parse_coordinates_from_path("invalid/coords")

        with pytest.raises(ValueError):
            Helpers.parse_coordinates_from_path("40.7128")  # Missing longitude

        with pytest.raises(ValueError):
            Helpers.parse_coordinates_from_path("40.7128/")  # Empty longitude

    def test_get_normalized_unit_default(self):
        """Test getting normalized unit with default value."""
        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = None
            unit = Helpers.get_normalized_unit()
            assert unit == DEFAULT_TEMP_UNIT

    def test_get_normalized_unit_celsius(self):
        """Test getting normalized unit for Celsius."""
        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "C"
            unit = Helpers.get_normalized_unit()
            assert unit == "C"

    def test_get_normalized_unit_fahrenheit(self):
        """Test getting normalized unit for Fahrenheit."""
        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "F"
            unit = Helpers.get_normalized_unit()
            assert unit == "F"

    def test_get_normalized_unit_lowercase(self):
        """Test getting normalized unit with lowercase input."""
        with patch("web.helpers.request") as mock_request:
            mock_request.form.get.return_value = "c"
            unit = Helpers.get_normalized_unit()
            assert unit == "C"

    def test_normalize_location_input_known_abbreviation(self):
        """Test normalizing location input with known abbreviations."""
        result = Helpers.normalize_location_input("UK")
        assert result == "United Kingdom"

        result = Helpers.normalize_location_input("USA")
        assert result == "United States"

        result = Helpers.normalize_location_input("UAE")
        assert result == "United Arab Emirates"

    def test_normalize_location_input_unknown_abbreviation(self):
        """Test normalizing location input with unknown abbreviations."""
        result = Helpers.normalize_location_input("Germany")
        assert result == "Germany"

        result = Helpers.normalize_location_input("XYZ")
        assert result == "XYZ"

    def test_get_date_range_for_query_tomorrow(self):
        """Test getting date range for 'tomorrow' query."""
        with patch("web.helpers.date") as mock_date:
            mock_today = date(2025, 5, 23)
            mock_date.today.return_value = mock_today

            dates = Helpers.get_date_range_for_query("tomorrow")
            expected = [date(2025, 5, 24)]
            assert dates == expected

    def test_get_date_range_for_query_this_weekend(self):
        """Test getting date range for 'this weekend' query."""
        with patch("web.helpers.date") as mock_date:
            # Mock a Friday (weekday 4)
            mock_today = date(2025, 5, 23)  # This is a Friday
            mock_date.today.return_value = mock_today

            dates = Helpers.get_date_range_for_query("this weekend")
            # Should return Saturday and Sunday
            expected = [date(2025, 5, 24), date(2025, 5, 25)]
            assert dates == expected

    def test_get_date_range_for_query_specific_weekday(self):
        """Test getting date range for specific weekday."""
        with patch("web.helpers.date") as mock_date:
            # Mock a Friday (weekday 4)
            mock_today = date(2025, 5, 23)
            mock_date.today.return_value = mock_today

            # Test Monday (should be next week)
            dates = Helpers.get_date_range_for_query("monday")
            expected = [date(2025, 5, 26)]  # Next Monday
            assert dates == expected

    def test_get_date_range_for_query_invalid(self):
        """Test getting date range for invalid query."""
        dates = Helpers.get_date_range_for_query("invalid query")
        assert dates == []


class TestConstants:
    """Test cases for web constants."""

    def test_location_abbreviation_mapping(self):
        """Test location abbreviation mapping constant."""
        assert isinstance(LOCATION_ABBREVIATION_MAPPING, dict)
        assert "UK" in LOCATION_ABBREVIATION_MAPPING
        assert "USA" in LOCATION_ABBREVIATION_MAPPING
        assert "UAE" in LOCATION_ABBREVIATION_MAPPING

    def test_weekday_names(self):
        """Test weekday names constant."""
        assert isinstance(WEEKDAY_NAMES, list)
        assert len(WEEKDAY_NAMES) == 7
        assert "monday" in WEEKDAY_NAMES
        assert "sunday" in WEEKDAY_NAMES

    def test_weekday_to_number(self):
        """Test weekday to number mapping."""
        assert isinstance(WEEKDAY_TO_NUMBER, dict)
        assert len(WEEKDAY_TO_NUMBER) == 7
        assert WEEKDAY_TO_NUMBER["monday"] == 0
        assert WEEKDAY_TO_NUMBER["sunday"] == 6

    def test_utils_constants(self):
        """Test utility constants."""
        assert DEFAULT_TEMP_UNIT in ["C", "F"]
        assert isinstance(VALID_TEMP_UNITS, (list, tuple))
        assert isinstance(TEMPERATURE_UNIT_CHOICES, (list, tuple))
        assert isinstance(FORECAST_DAYS_CHOICES, (list, tuple))

    def test_temperature_unit_choices_format(self):
        """Test temperature unit choices format."""
        for choice in TEMPERATURE_UNIT_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert choice[0] in ["C", "F"]

    def test_forecast_days_choices_format(self):
        """Test forecast days choices format."""
        for choice in FORECAST_DAYS_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert isinstance(choice[0], int)
            assert choice[0] > 0
