"""Tests for the LocationManager class."""

from unittest.mock import MagicMock, patch

import pytest

from weather_app.location import LocationManager


@pytest.fixture
def location_manager():
    """Create a LocationManager instance with mocked dependencies."""
    mock_api = MagicMock()
    mock_display = MagicMock()

    # Create location manager
    manager = LocationManager(mock_api, mock_display)

    return manager


def test_location_manager_initialization(location_manager):
    """Test that LocationManager initializes correctly."""
    assert location_manager is not None


@patch("weather_app.location.get_location")
def test_get_location_wrapper(mock_get_location, location_manager):
    """Test that LocationManager.get_location calls the global function."""
    mock_get_location.return_value = "51.52,-0.11"

    result = location_manager.get_location()

    assert mock_get_location.called
    assert result == "51.52,-0.11"


@patch("weather_app.location.get_favorite_locations")
def test_get_favorite_locations_wrapper(
    mock_get_favorites, location_manager, sample_location
):
    """Test that LocationManager.get_favorite_locations calls the function."""
    mock_get_favorites.return_value = [sample_location]

    result = location_manager.get_favorite_locations()

    assert mock_get_favorites.called
    assert result == [sample_location]


@patch("weather_app.location.toggle_favorite")
def test_toggle_favorite_wrapper(mock_toggle_favorite, location_manager):
    """Test that LocationManager.toggle_favorite calls the global function."""
    mock_toggle_favorite.return_value = True

    result = location_manager.toggle_favorite(1)

    assert mock_toggle_favorite.called
    mock_toggle_favorite.assert_called_with(1)
    assert result is True


@patch("weather_app.location.get_coordinates")
def test_get_coordinates_wrapper(mock_get_coordinates, location_manager):
    """Test that LocationManager.get_coordinates calls the global function."""
    mock_get_coordinates.return_value = (51.52, -0.11)

    result = location_manager.get_coordinates("London")

    assert mock_get_coordinates.called
    mock_get_coordinates.assert_called_with("London")
    assert result == (51.52, -0.11)


@patch("weather_app.location.save_location_to_db")
def test_save_location_to_db_function(mock_save_location, sample_location):
    """Test the save_location_to_db function directly."""
    # Configure mock to return location data
    mock_save_location.return_value = {
        "id": sample_location.id,
        "name": sample_location.name,
        "lat": sample_location.latitude,
        "lon": sample_location.longitude,
        "country": sample_location.country,
        "region": sample_location.region,
    }

    # Create location data
    location_data = {
        "name": "London",
        "lat": 51.52,
        "lon": -0.11,
        "country": "United Kingdom",
        "region": "Greater London",
    }

    # Import and call the function
    from weather_app.location import save_location_to_db

    result = save_location_to_db(location_data)

    # Check that the function was called
    assert mock_save_location.called

    # Check the result
    assert result is not None
    assert result["lat"] == 51.52
    assert result["lon"] == -0.11


@patch("weather_app.location._get_location_repo")
def test_get_favorite_locations_function(mock_get_location_repo, sample_location):
    """Test the get_favorite_locations function directly."""
    # Configure mock repository
    mock_repo = MagicMock()
    mock_repo.get_favorites.return_value = [sample_location]
    mock_get_location_repo.return_value = mock_repo

    # Import and call the function
    from weather_app.location import get_favorite_locations

    result = get_favorite_locations()

    # Check that the repository method was called
    assert mock_repo.get_favorites.called

    # Check the result
    assert result == [sample_location]
