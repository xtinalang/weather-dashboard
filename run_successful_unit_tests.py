#!/usr/bin/env python3
"""
Demonstration of successful unit tests for the Flask web UI.
This script runs individual unit tests to show they work correctly.
"""

import sys
import traceback


def test_constants():
    """Test constants are properly defined and accessible."""
    print("🧪 Testing Constants...")

    try:
        from web.helpers import (
            LOCATION_ABBREVIATION_MAPPING,
            WEEKDAY_NAMES,
            WEEKDAY_TO_NUMBER,
        )
        from web.utils import (
            DEFAULT_TEMP_UNIT,
            TEMPERATURE_UNIT_CHOICES,
            VALID_TEMP_UNITS,
        )

        # Test location abbreviation mapping
        assert isinstance(LOCATION_ABBREVIATION_MAPPING, dict)
        assert len(LOCATION_ABBREVIATION_MAPPING) > 0
        assert "UK" in LOCATION_ABBREVIATION_MAPPING
        assert LOCATION_ABBREVIATION_MAPPING["UK"] == "United Kingdom"

        # Test weekday constants
        assert isinstance(WEEKDAY_NAMES, list)
        assert len(WEEKDAY_NAMES) == 7
        assert "monday" in WEEKDAY_NAMES
        assert "sunday" in WEEKDAY_NAMES

        # Test weekday mapping
        assert isinstance(WEEKDAY_TO_NUMBER, dict)
        assert len(WEEKDAY_TO_NUMBER) == 7
        assert WEEKDAY_TO_NUMBER["monday"] == 0
        assert WEEKDAY_TO_NUMBER["sunday"] == 6

        # Test temperature constants
        assert DEFAULT_TEMP_UNIT in ["C", "F"]
        assert isinstance(VALID_TEMP_UNITS, (list, tuple))
        assert isinstance(TEMPERATURE_UNIT_CHOICES, (list, tuple))

        print("   ✅ All constants tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Constants test failed: {e}")
        return False


def test_helper_functions():
    """Test helper functions work correctly."""
    print("🧪 Testing Helper Functions...")

    try:
        from web.helpers import Helpers

        # Test coordinate parsing - positive coordinates
        lat, lon = Helpers.parse_coordinates_from_path("40.7128/-74.0060")
        assert lat == 40.7128
        assert lon == -74.0060

        # Test coordinate parsing - negative coordinates
        lat, lon = Helpers.parse_coordinates_from_path("-33.8688/151.2093")
        assert lat == -33.8688
        assert lon == 151.2093

        # Test location normalization
        result = Helpers.normalize_location_input("Germany")
        assert result == "Germany"  # Should return unchanged for unknown

        result = Helpers.normalize_location_input("XYZ")
        assert result == "XYZ"  # Should return unchanged for unknown

        print("   ✅ All helper function tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Helper function test failed: {e}")
        return False


def test_coordinate_parsing_errors():
    """Test coordinate parsing handles errors correctly."""
    print("🧪 Testing Error Handling...")

    try:
        from web.helpers import Helpers

        # Test invalid coordinates raise ValueError
        try:
            Helpers.parse_coordinates_from_path("invalid/coords")
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass  # Expected

        try:
            Helpers.parse_coordinates_from_path("40.7128")  # Missing longitude
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass  # Expected

        try:
            Helpers.parse_coordinates_from_path("40.7128/")  # Empty longitude
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass  # Expected

        print("   ✅ All error handling tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False


def test_location_functions():
    """Test location functions with mocking."""
    print("🧪 Testing Location Functions...")

    try:
        from unittest.mock import MagicMock, patch

        from weather_app.location import get_favorite_locations, toggle_favorite
        from weather_app.models import Location

        # Test get_favorite_locations with mocked repo
        with patch("weather_app.location._get_location_repo") as mock_repo_func:
            mock_repo = MagicMock()
            mock_repo_func.return_value = mock_repo

            # Mock favorite locations
            favorite_locations = [
                Location(
                    name="London", latitude=51.5074, longitude=-0.1278, is_favorite=True
                ),
                Location(
                    name="Paris", latitude=48.8566, longitude=2.3522, is_favorite=True
                ),
            ]
            mock_repo.get_favorites.return_value = favorite_locations

            # Call function
            result = get_favorite_locations()

            # Verify
            assert result == favorite_locations
            assert len(result) == 2
            mock_repo.get_favorites.assert_called_once()

        # Test toggle_favorite when location not found
        with patch("weather_app.location._get_location_repo") as mock_repo_func:
            mock_repo = MagicMock()
            mock_repo_func.return_value = mock_repo
            mock_repo.get_by_id.return_value = None  # Location not found

            # Call function
            result = toggle_favorite(999)

            # Should return False when location not found
            assert result is False
            mock_repo.get_by_id.assert_called_once_with(999)
            mock_repo.update.assert_not_called()

        print("   ✅ All location function tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Location function test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all unit tests and show results."""
    print("=" * 60)
    print("🎯 UNIT TESTS DEMONSTRATION - Flask Web UI")
    print("=" * 60)
    print()

    tests = [
        test_constants,
        test_helper_functions,
        test_coordinate_parsing_errors,
        test_location_functions,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        if test_func():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 RESULTS: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 ALL UNIT TESTS PASSED SUCCESSFULLY!")
        print()
        print("✅ What we've demonstrated:")
        print("   • Constants are properly defined and accessible")
        print("   • Helper functions work correctly in isolation")
        print("   • Error handling works as expected")
        print("   • Location functions can be mocked and tested")
        print("   • Pure functions are fast and reliable")
        print("   • Proper separation of concerns")
        return 0
    else:
        print("❌ Some tests failed - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
