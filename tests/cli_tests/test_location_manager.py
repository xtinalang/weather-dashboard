"""Tests for the LocationManager class."""

from unittest.mock import MagicMock, patch

import pytest

from weather_app.location import LocationManager


@pytest.fixture
def mock_user_input():
    """Create a mocked User_Input_Information instance."""
    mock = MagicMock()
    # Configure default method behaviors
    mock.get_location_method.return_value = "1"  # Search method
    mock.get_search_query.return_value = "London"
    mock.get_location_selection.return_value = "1"  # First result
    mock.get_direct_location.return_value = "Paris, France"
    return mock


@pytest.fixture
def location_manager(mock_api, mock_display, mock_location_repo):
    """Create a LocationManager instance with mocked dependencies."""
    with patch("weather_app.location.User_Input_Information") as mock_input_class:
        # Mock return instance
        mock_input = MagicMock()
        mock_input_class.return_value = mock_input

        # Create location manager
        manager = LocationManager(mock_api, mock_display)

        # Replace repository with mock
        manager.location_repo = mock_location_repo

        # Replace user_input with mock
        manager.user_input = mock_input

        return manager, mock_input


def test_get_location_search_method(location_manager):
    """Test get_location using search method."""
    manager, mock_input = location_manager

    # Configure input to use search method
    mock_input.get_location_method.return_value = "1"

    # Configure search result selection
    mock_input.get_search_query.return_value = "London"
    mock_input.get_location_selection.return_value = "1"

    # Call the method
    result = manager.get_location()

    # Check that the correct methods were called
    assert mock_input.get_location_method.called
    assert mock_input.get_search_query.called
    assert manager.weather_api.search_city.called
    assert mock_input.get_location_selection.called

    # Check the result
    assert result is not None
    assert "51.52,-0.11" in result


def test_get_location_direct_method(location_manager):
    """Test get_location using direct method."""
    manager, mock_input = location_manager

    # Configure input to use direct method
    mock_input.get_location_method.return_value = "2"
    mock_input.get_direct_location.return_value = "Paris, France"

    # Call the method
    result = manager.get_location()

    # Check that the correct methods were called
    assert mock_input.get_location_method.called
    assert mock_input.get_direct_location.called
    assert manager.weather_api.search_city.called

    # Check the result
    assert result is not None
    assert "51.52,-0.11" in result  # Using our mock API response


def test_save_location_to_db_new_location(location_manager, sample_location):
    """Test saving a new location to the database."""
    manager, _ = location_manager

    # Configure repository to not find existing location
    manager.location_repo.find_by_coordinates.return_value = None
    manager.location_repo.create.return_value = sample_location

    # Create location data
    location_data = {
        "name": "London",
        "lat": 51.52,
        "lon": -0.11,
        "country": "United Kingdom",
        "region": "Greater London",
    }

    # Call the method
    result = manager._save_location_to_db(location_data)

    # Check that the repository methods were called
    assert manager.location_repo.find_by_coordinates.called
    assert manager.location_repo.create.called

    # Check the result
    assert result is not None
    assert "id" in result
    assert result["lat"] == float(location_data["lat"])
    assert result["lon"] == float(location_data["lon"])


def test_save_location_to_db_existing_location(location_manager, sample_location):
    """Test saving an existing location to the database."""
    manager, _ = location_manager

    # Configure repository to find existing location
    manager.location_repo.find_by_coordinates.return_value = sample_location

    # Create location data
    location_data = {
        "name": "London",
        "lat": 51.52,
        "lon": -0.11,
        "country": "United Kingdom",
        "region": "Greater London",
    }

    # Call the method
    result = manager._save_location_to_db(location_data)

    # Check that the repository methods were called
    assert manager.location_repo.find_by_coordinates.called
    assert not manager.location_repo.create.called

    # Check the result
    assert result is not None
    assert "id" in result
    assert result["lat"] == float(location_data["lat"])
    assert result["lon"] == float(location_data["lon"])


def test_get_favorite_locations(location_manager, sample_location):
    """Test getting favorite locations."""
    manager, _ = location_manager

    # Configure repository to return locations
    manager.location_repo.get_favorites.return_value = [sample_location]

    # Call the method
    result = manager.get_favorite_locations()

    # Check that the repository method was called
    assert manager.location_repo.get_favorites.called

    # Check the result
    assert result is not None
    assert len(result) == 1
    assert result[0].id == sample_location.id


def test_toggle_favorite_success(location_manager, sample_location):
    """Test toggling favorite status successfully."""
    manager, _ = location_manager

    # Configure repository to find location and update
    manager.location_repo.get_by_id.return_value = sample_location
    manager.location_repo.update.return_value = sample_location

    # Call the method
    result = manager.toggle_favorite(sample_location.id)

    # Check that the repository methods were called
    assert manager.location_repo.get_by_id.called
    assert manager.location_repo.update.called

    # Check the result
    assert result is True


def test_toggle_favorite_location_not_found(location_manager):
    """Test toggling favorite status with location not found."""
    manager, _ = location_manager

    # Configure repository to not find location
    manager.location_repo.get_by_id.return_value = None

    # Call the method
    result = manager.toggle_favorite(999)  # Non-existent ID

    # Check that the repository method was called
    assert manager.location_repo.get_by_id.called
    assert not manager.location_repo.update.called

    # Check the result
    assert result is False
