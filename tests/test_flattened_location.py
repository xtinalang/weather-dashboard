"""Unit tests for flattened location functions."""

from unittest.mock import MagicMock, patch

from weather_app.location import (
    get_coordinates,
    get_favorite_locations,
    get_location,
    save_location_to_db,
    toggle_favorite,
)
from weather_app.models import Location


class TestLocationFunctions:
    """Test cases for location functions."""

    def test_get_location_with_mocked_dependencies(self):
        """Test get_location function with mocked dependencies."""
        with (
            patch("weather_app.location._get_weather_api") as mock_api_func,
            patch("weather_app.location._get_display") as mock_display_func,
            patch("weather_app.location._get_user_input") as mock_input_func,
        ):
            # Setup mocks
            mock_api = MagicMock()
            mock_display = MagicMock()
            mock_input = MagicMock()

            mock_api_func.return_value = mock_api
            mock_display_func.return_value = mock_display
            mock_input_func.return_value = mock_input

            # Mock API response
            mock_location_data = {
                "name": "London",
                "region": "England",
                "country": "United Kingdom",
                "lat": 51.5074,
                "lon": -0.1278,
            }
            mock_api.get_location.return_value = mock_location_data

            # Call function
            result = get_location("London")

            # Verify API was called with correct parameters
            mock_api.get_location.assert_called_once_with("London")

            # Verify result
            assert result == mock_location_data

    def test_save_location_to_db_with_mocked_repo(self):
        """Test save_location_to_db function with mocked repository."""
        with patch("weather_app.location._get_location_repo") as mock_repo_func:
            mock_repo = MagicMock()
            mock_repo_func.return_value = mock_repo

            # Mock save operation
            mock_location = Location(
                name="Paris", latitude=48.8566, longitude=2.3522, is_favorite=False
            )
            mock_repo.save.return_value = mock_location

            # Call function
            result = save_location_to_db("Paris", 48.8566, 2.3522)

            # Verify repository was called
            mock_repo.save.assert_called_once()

            # Verify the result is the expected location
            assert result == mock_location

            # Verify correct location was created
            call_args = mock_repo.save.call_args[0][0]
            assert call_args.name == "Paris"
            assert call_args.latitude == 48.8566
            assert call_args.longitude == 2.3522
            assert call_args.is_favorite is False

    def test_get_favorite_locations_with_mocked_repo(self):
        """Test get_favorite_locations function with mocked repository."""
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

    def test_toggle_favorite_success(self):
        """Test toggle_favorite function with successful toggle."""
        with patch("weather_app.location._get_location_repo") as mock_repo_func:
            mock_repo = MagicMock()
            mock_repo_func.return_value = mock_repo

            # Mock location exists
            mock_location = Location(
                id=1,
                name="Tokyo",
                latitude=35.6762,
                longitude=139.6503,
                is_favorite=False,
            )
            mock_repo.get_by_id.return_value = mock_location

            # Call function
            result = toggle_favorite(1)

            # Verify
            assert result is True
            mock_repo.get_by_id.assert_called_once_with(1)
            assert mock_location.is_favorite is True
            mock_repo.update.assert_called_once_with(mock_location)

    def test_toggle_favorite_location_not_found(self):
        """Test toggle_favorite function when location not found."""
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

    def test_get_coordinates_with_mocked_api(self):
        """Test get_coordinates function with mocked API."""
        with patch("weather_app.location._get_weather_api") as mock_api_func:
            mock_api = MagicMock()
            mock_api_func.return_value = mock_api

            # Mock successful API response
            mock_location_data = {
                "lat": 40.7128,
                "lon": -74.0060,
            }
            mock_api.get_location.return_value = mock_location_data

            # Call function
            result = get_coordinates("New York")

            # Verify
            assert result == (40.7128, -74.0060)
            mock_api.get_location.assert_called_once_with("New York")

    def test_get_coordinates_api_failure(self):
        """Test get_coordinates function when API fails."""
        with patch("weather_app.location._get_weather_api") as mock_api_func:
            mock_api = MagicMock()
            mock_api_func.return_value = mock_api
            mock_api.get_location.side_effect = Exception("API Error")

            # Call function
            result = get_coordinates("Invalid Location")

            # Should return None when API fails
            assert result is None
            mock_api.get_location.assert_called_once_with("Invalid Location")


class TestSingletonBehavior:
    """Test singleton behavior of module-level instances."""

    def test_weather_api_singleton(self):
        """Test weather API instance is singleton."""
        with patch("weather_app.location.WeatherAPI") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Import function that uses the singleton
            from weather_app.location import _get_weather_api

            # Call multiple times
            api1 = _get_weather_api()
            api2 = _get_weather_api()

            # Should be the same instance
            assert api1 is api2
            mock_class.assert_called_once()

    def test_location_repo_singleton(self):
        """Test location repository instance is singleton."""
        with patch("weather_app.location.LocationRepository") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Import function that uses the singleton
            from weather_app.location import _get_location_repo

            # Call multiple times
            repo1 = _get_location_repo()
            repo2 = _get_location_repo()

            # Should be the same instance
            assert repo1 is repo2
            mock_class.assert_called_once()

    def test_display_singleton(self):
        """Test display instance is singleton."""
        with patch("weather_app.location.Display") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Import function that uses the singleton
            from weather_app.location import _get_display

            # Call multiple times
            display1 = _get_display()
            display2 = _get_display()

            # Should be the same instance
            assert display1 is display2
            mock_class.assert_called_once()

    def test_user_input_singleton(self):
        """Test user input instance is singleton."""
        with patch("weather_app.location.UserInput") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Import function that uses the singleton
            from weather_app.location import _get_user_input

            # Call multiple times
            input1 = _get_user_input()
            input2 = _get_user_input()

            # Should be the same instance
            assert input1 is input2
            mock_class.assert_called_once()
