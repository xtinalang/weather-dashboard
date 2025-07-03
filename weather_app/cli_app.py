# Main WeatherApp (application orchestration)
import logging
from datetime import datetime

from .api import WeatherAPI
from .current import CurrentWeatherManager
from .database import Database
from .display import WeatherDisplay
from .exceptions import DetachedInstanceError, SessionError
from .forecast import ForecastManager
from .location import LocationManager
from .models import Location
from .repository import LocationRepository, SettingsRepository
from .user_input import User_Input_Information
from .weather_types import TemperatureUnit

logger = logging.getLogger("weather_app")


class WeatherApp:
    def __init__(self) -> None:
        # Initialize database
        self.db = Database()

        # Initialize components
        self.weather_api = WeatherAPI()
        self.display = WeatherDisplay()
        self.location_manager = LocationManager(self.weather_api, self.display)
        self.forecast_manager = ForecastManager(self.weather_api, self.display)
        self.current_manager = CurrentWeatherManager(self.weather_api, self.display)
        self.location_repo = LocationRepository()
        self.settings_repo = SettingsRepository()
        self.unit: TemperatureUnit = "C"  # Default to Celsius
        self.user_input = User_Input_Information

    def _return_fresh_location(self, location: Location) -> Location:
        """
        Create a fresh Location object detached from any session.
        This helps avoid SQLAlchemy session issues.
        """
        return Location(
            id=location.id,
            name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            country=location.country,
            region=location.region,
            is_favorite=location.is_favorite,
            created_at=datetime.now()
            if not hasattr(location, "created_at")
            else location.created_at,
            updated_at=datetime.now(),
        )

    def refresh_location(self, location: Location) -> Location | None:
        try:
            location_name = location.name if hasattr(location, "name") else "Unknown"
            location_id = location.id if hasattr(location, "id") else "Unknown"
            logger.debug(f"Refreshing location: {location_name} (ID: {location_id})")

            # Method 1: Try to use the repository's find_or_create method directly
            if hasattr(location, "latitude") and hasattr(location, "longitude"):
                try:
                    name = getattr(location, "name", "Unknown Location")
                    country = getattr(location, "country", "Unknown")
                    region = getattr(location, "region", None)

                    logger.debug(
                        f"Using find_or_create for {name} at "
                        f"{location.latitude}, {location.longitude}"
                    )

                    # This will either find the existing location or create a new
                    # one with these coordinates
                    return self.location_repo.find_or_create_by_coordinates(
                        name=name,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        country=country,
                        region=region,
                    )
                except Exception as e:
                    logger.warning(f"Error using find_or_create method: {e}")

            # Method 2: Get by ID if available
            if hasattr(location, "id") and location.id is not None:
                try:
                    logger.debug(f"Trying to refresh by ID: {location.id}")
                    fresh_location = self.location_repo.get_by_id(location.id)
                    if fresh_location:
                        logger.debug(
                            f"Refreshed location by ID: {fresh_location.name} "
                            f"(ID: {fresh_location.id})"
                        )
                        return self._return_fresh_location(fresh_location)
                    else:
                        logger.warning(
                            f"Location with ID {location.id} not found in database"
                        )
                except Exception as e:
                    logger.warning(f"Error refreshing location by ID: {e}")

            # Method 3: Find by coordinates
            if hasattr(location, "latitude") and hasattr(location, "longitude"):
                try:
                    logger.debug(
                        f"Trying to refresh by coordinates: "
                        f"{location.latitude}, {location.longitude}"
                    )
                    fresh_location = self.location_repo.find_by_coordinates(
                        location.latitude, location.longitude
                    )
                    if fresh_location:
                        logger.debug(
                            f"Successfully refreshed location by coordinates: "
                            f"{fresh_location.name} (ID: {fresh_location.id})"
                        )
                        return self._return_fresh_location(fresh_location)
                    else:
                        logger.warning(
                            f"Location with coordinates {location.latitude}, "
                            f"{location.longitude} not found"
                        )
                except Exception as e:
                    logger.warning(f"Error refreshing location by coordinates: {e}")

            # Method 4: Create a new location if all else fails
            if (
                hasattr(location, "name")
                and hasattr(location, "latitude")
                and hasattr(location, "longitude")
            ):
                try:
                    logger.debug(
                        f"Creating new location as last resort: {location.name}"
                    )

                    # Extract all attributes safely
                    name = getattr(location, "name", "Unknown")
                    country = getattr(location, "country", "Unknown")
                    region = getattr(location, "region", None)

                    # Create a new location
                    new_location = self.location_repo.find_or_create_by_coordinates(
                        name=name,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        country=country,
                        region=region,
                    )

                    logger.debug(
                        f"Created new location as last resort: {new_location.name} "
                        f"(ID: {new_location.id})"
                    )
                    return new_location

                except Exception as e:
                    logger.error(f"Error creating new location as last resort: {e}")

            logger.warning("Could not refresh location by any method")
            return None

        except DetachedInstanceError as e:
            logger.error(f"Detached instance error in refresh_location: {e}")
            return None
        except SessionError as e:
            logger.error(f"Session error in refresh_location: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in refresh_location: {e}")
            return None

    def run(self) -> None:
        """Main application loop"""
        try:
            # Get location coordinates from user input
            coords = self.location_manager.get_location()
            if not coords:
                return

            # Parse coordinates
            lat, lon = map(float, coords.split(","))

            # Get a fresh copy of the location directly from the repository
            location = self.location_repo.find_by_coordinates(lat, lon)
            if not location:
                logger.error(
                    f"Location with coordinates {lat},{lon} not found in database"
                )
                self.display.show_error("Error retrieving location")
                return

            # Refresh the location to ensure it's attached to a session
            location = self.refresh_location(location)
            if not location:
                logger.error("Could not refresh location")
                self.display.show_error("Error retrieving location")
                return

            # Show current weather
            self._show_current_weather(location)

            # Show forecast based on user settings

            self.forecast_manager.get_forecast(location)

        except Exception as e:
            logger.error(f"Application error: {e}")
            self.display.show_error("An error occurred while running the application")

    def show_forecast_for_days(self, days: int) -> None:
        """Show forecast for a specific number of days"""
        try:
            # Get location coordinates from user input
            coords = self.location_manager.get_location()
            if not coords:
                return

            # Parse coordinates
            lat, lon = map(float, coords.split(","))

            # Get a fresh copy of the location directly from the repository
            location = self.location_repo.find_by_coordinates(lat, lon)
            if not location:
                logger.error(
                    f"Location with coordinates {lat},{lon} not found in database"
                )
                self.display.show_error("Error retrieving location")
                return

            # Refresh the location to ensure it's attached to a session
            location = self.refresh_location(location)
            if not location:
                logger.error("Could not refresh location")
                self.display.show_error("Error retrieving location")
                return

            self.forecast_manager.get_forecast(location, days=days)
        except Exception as e:
            logger.error(f"Error showing forecast: {e}")
            self.display.show_error("Failed to show forecast")

    def show_forecast_for_date(self, target_date: datetime) -> None:
        """Show forecast for a specific date"""
        try:
            # Get location coordinates from user input
            coords = self.location_manager.get_location()
            if not coords:
                return

            # Parse coordinates
            lat, lon = map(float, coords.split(","))

            # Get a fresh copy of the location directly from the repository
            location = self.location_repo.find_by_coordinates(lat, lon)
            if not location:
                logger.error(
                    f"Location with coordinates {lat},{lon} not found in database"
                )
                self.display.show_error("Error retrieving location")
                return

            # Refresh the location to ensure it's attached to a session
            location = self.refresh_location(location)
            if not location:
                logger.error("Could not refresh location")
                self.display.show_error("Error retrieving location")
                return

            self.forecast_manager.get_forecast_for_day(location, target_date)
        except Exception as e:
            logger.error(f"Error showing forecast for date: {e}")
            self.display.show_error("Failed to show forecast for the specified date")

    def set_default_forecast_days(self, days: int) -> None:
        """Set the default number of forecast days"""
        self.forecast_manager.update_forecast_days(days)

    def _show_current_weather(self, location: Location) -> None:
        """Show current weather for a location"""
        try:
            # Use the current manager to get and display current weather
            self.current_manager.get_current_weather(location)
        except Exception as e:
            logger.error(f"Error showing current weather: {e}")
            self.display.show_error("Failed to get current weather")

    def run_from_user_input(self) -> None:
        """Main application flow"""
        print("Welcome to the Weather App!")
        print("==========================")

        # Set temperature unit based on user preference
        unit_choice = self.user_input.get_temperature_choice()
        if unit_choice == "2":
            self.unit = "F"
        else:
            self.unit = "C"

        try:
            # Get location coordinates from user input
            coords = self.location_manager.get_location()
            if not coords:
                logger.warning("No location selected")
                print("No location selected. Exiting application.")
                return

            # Parse coordinates
            try:
                lat, lon = map(float, coords.split(","))
                logger.debug(f"Parsed coordinates: lat={lat}, lon={lon}")
            except Exception as e:
                logger.error(f"Failed to parse coordinates '{coords}': {e}")
                print(
                    f"Invalid coordinates format: {coords}. "
                    f"Expected format: 'latitude,longitude'"
                )
                return

            # Get a fresh copy of the location directly from the repository
            try:
                logger.debug(f"Attempting to find location by coordinates: {lat},{lon}")
                location = self.location_repo.find_by_coordinates(lat, lon)
                if not location:
                    logger.error(
                        f"Location with coordinates {lat},{lon} not found in database"
                    )
                    print(
                        f"Location with coordinates {lat},{lon} not found. "
                        f"Please try a different location."
                    )
                    return
                logger.debug(f"Found location: {location.name} (ID: {location.id})")
            except Exception as e:
                logger.error(f"Error finding location by coordinates: {e}")
                print(f"Error retrieving location: {e}")
                return

            # Refresh the location to ensure it's attached to a session
            try:
                logger.debug(
                    f"Attempting to refresh location: {location.name} "
                    f"(ID: {location.id})"
                )
                location = self.refresh_location(location)
                if not location:
                    logger.error("Could not refresh location")
                    print("Error: Could not refresh location data. Please try again.")
                    return
                logger.debug(
                    f"Successfully refreshed location: {location.name} "
                    f"(ID: {location.id})"
                )
            except Exception as e:
                logger.error(f"Error refreshing location: {e}")
                print(f"Error refreshing location data: {e}")
                return

            logger.info(f"Found location: {location.name}, {location.country}")

            # Now we have a fresh location object within a session
            logger.info(
                f"Fetching weather for coordinates: "
                f"{location.latitude},{location.longitude}"
            )

            # Get and display current weather
            try:
                self.current_manager.get_current_weather(location)
            except Exception as e:
                logger.error(f"Error getting current weather: {e}")
                print(f"Error retrieving current weather: {e}")

            # Get and display forecast
            try:
                self.forecast_manager.get_forecast(location, unit=self.unit)
            except Exception as e:
                logger.error(f"Error getting forecast: {e}")
                print(f"Error retrieving forecast: {e}")

        except KeyboardInterrupt:
            logger.info("Application terminated by user")
            print("\nApplication terminated by user.")
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
            print("Please check the log for more information.")
