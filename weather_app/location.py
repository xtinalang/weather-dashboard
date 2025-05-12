import logging
from typing import Optional, cast

from .api import WeatherAPI
from .database import init_db
from .display import WeatherDisplay
from .models import Location
from .repository import LocationRepository
from .schema import LocationData
from .user_input import User_Input_Information

logger = logging.getLogger("weather_app")


class LocationManager:
    def __init__(self, weather_api: WeatherAPI, display: WeatherDisplay) -> None:
        self.weather_api: WeatherAPI = weather_api
        self.display: WeatherDisplay = display
        self.user_input: User_Input_Information = User_Input_Information()
        self.location_repo: LocationRepository = LocationRepository()

    def get_location(self) -> str | None:
        """
        Get location coordinates from user input or database

        Returns:
            String with "latitude,longitude" format or None if cancelled
        """
        try:
            # Check if database is initialized and has locations
            self._check_database()

            while True:
                method: str = self.user_input.get_location_method()
                if method == "1":
                    return self._search_location()
                elif method == "2":
                    return self._direct_location()
                elif method == "3":  # Add an option to use saved locations
                    return self._use_saved_location()
                elif method.lower() == "q":
                    return None
        except Exception as e:
            logger.error(f"Error in get_location: {e}")
            self.display.show_error(f"Error retrieving location: {e}")
            return None

    def _check_database(self) -> None:
        """Check if database is initialized, initialize if needed"""
        try:
            # Try to count locations
            count: int = self.location_repo.count()
            logger.debug(f"Database initialized with {count} locations")
        except Exception as e:
            logger.warning(f"Database may not be initialized: {e}")
            print("Database not initialized. Attempting to initialize...")
            try:
                init_db()
                print("Database initialized successfully!")
            except Exception as init_err:
                logger.error(f"Failed to initialize database: {init_err}")
                print(f"Error initializing database: {init_err}")
                print(
                    "Please run 'python -m weather_app init-db' to initialize the database"
                )

    def _search_location(self) -> str | None:
        """
        Search for a location by name

        Returns:
            String with "latitude,longitude" format or None if cancelled
        """
        max_attempts: int = 3
        for _ in range(max_attempts):
            try:
                query: str = self.user_input.get_search_query()
                if not query:
                    continue

                logger.debug(f"Searching for location: {query}")
                city_list: list[LocationData] | None = cast(
                    list[LocationData] | None, self.weather_api.search_city(query)
                )

                if not city_list:
                    logger.warning(f"No results found for query: {query}")
                    print(
                        f"No cities found matching '{query}'. Please try a different search term."
                    )
                    continue

                self.display.show_city(city_list)
                selection: str = self.user_input.get_location_selection(len(city_list))

                if selection.lower() == "q":
                    return None

                if selection.isdigit():
                    idx: int = int(selection) - 1
                    if 0 <= idx < len(city_list):
                        selected: LocationData = city_list[idx]
                        logger.debug(
                            f"Selected location: {selected['name']}, {selected['country']}"
                        )

                        # Save the selected location to the database
                        location_info: LocationData = self._save_location_to_db(
                            selected
                        )
                        if "id" in location_info:
                            logger.debug(
                                f"Location saved with ID: {location_info['id']}"
                            )

                        lat: float | str = selected["lat"]
                        lon: float | str = selected["lon"]
                        return f"{lat},{lon}"
                    else:
                        print(
                            f"Invalid selection. Please enter a number between 1 and {len(city_list)}."
                        )
            except Exception as e:
                logger.error(f"Error in location search: {e}")
                print(f"Error searching for location: {e}")

        print("Maximum search attempts reached. Please try again later.")
        return None

    def _direct_location(self) -> str | None:
        """
        Enter a location directly

        Returns:
            String with "latitude,longitude" format or None if cancelled
        """
        max_attempts: int = 3
        for _ in range(max_attempts):
            try:
                location: str = self.user_input.get_direct_location()
                if not location:
                    continue

                logger.debug(f"Searching for direct location: {location}")
                results: list[LocationData] | None = cast(
                    list[LocationData] | None, self.weather_api.search_city(location)
                )

                if not results:
                    logger.warning(f"No results found for direct location: {location}")
                    print(
                        f"No cities found matching '{location}'. Please try a different location."
                    )
                    continue

                self.display.show_city(results)

                # Ask user to confirm
                print("\nIs this the correct location? (y/n)")
                confirm: str = input("> ").lower()
                if confirm != "y":
                    continue

                # Save the first result to the database
                location_info: LocationData = self._save_location_to_db(results[0])
                if "id" in location_info:
                    logger.debug(f"Location saved with ID: {location_info['id']}")

                lat: float | str = results[0]["lat"]
                lon: float | str = results[0]["lon"]
                return f"{lat},{lon}"
            except Exception as e:
                logger.error(f"Error in direct location: {e}")
                print(f"Error finding location: {e}")

        print("Maximum location attempts reached. Please try again later.")
        return None

    def _use_saved_location(self) -> str | None:
        """
        Use a previously saved location

        Returns:
            String with "latitude,longitude" format or None if cancelled
        """
        try:
            # Get favorite locations first
            favorites: list[Location] = self.location_repo.get_favorites()

            # If no favorites, get all locations
            locations: list[Location]
            if not favorites:
                locations = self.location_repo.get_all(limit=10)
            else:
                locations = favorites

            if not locations:
                print("No saved locations found. Please search for a location first.")
                return self._search_location()

            # Display saved locations
            print("\nSaved locations:")
            print("=" * 50)
            for i, loc in enumerate(locations, 1):
                star: str = "★" if loc.is_favorite else " "
                region_str: str = loc.region or "N/A"
                print(f"{i}. {star} {loc.name}, {region_str}, {loc.country}")
                print(f"   Lat: {loc.latitude}, Lon: {loc.longitude}")
                print("-" * 50)

            # Get user selection
            print(f"Select a location (1-{len(locations)}) or 'q' to go back:")
            selection: str = input("> ")

            if selection.lower() == "q":
                return None

            if selection.isdigit():
                idx: int = int(selection) - 1
                if 0 <= idx < len(locations):
                    selected: Location = locations[idx]
                    logger.debug(
                        f"Selected saved location: {selected.name}, {selected.country}"
                    )
                    return f"{selected.latitude},{selected.longitude}"
                else:
                    print(
                        f"Invalid selection. Please enter a number between 1 and {len(locations)}."
                    )

            # If we get here, the selection was invalid
            print("Invalid selection. Please try again.")
            return self._use_saved_location()
        except Exception as e:
            logger.error(f"Error getting saved locations: {e}")
            print(f"Error retrieving saved locations: {e}")
            return None

    def _save_location_to_db(self, location_data: LocationData) -> LocationData:
        """
        Save a location to the database if it doesn't already exist

        Args:
            location_data: Dictionary with location data from API

        Returns:
            Dictionary with location data rather than the Location object
            to avoid session binding issues.
        """
        try:
            # Extract and validate data
            name: str = location_data.get("name", "Unknown")

            latitude: float
            longitude: float
            try:
                lat_value = location_data.get("lat", 0)
                lon_value = location_data.get("lon", 0)
                latitude = float(lat_value)
                longitude = float(lon_value)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid coordinates in location data: {e}")
                raise ValueError(f"Invalid coordinates: {e}") from e

            country: str = location_data.get("country", "Unknown")
            region: Optional[str] = location_data.get("region")

            logger.debug(f"Saving location: {name} at {latitude}, {longitude}")

            # Use the find_or_create method to handle this more robustly
            try:
                location: Location = self.location_repo.find_or_create_by_coordinates(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    country=country,
                    region=region,
                )

                # Return a dictionary with the location data
                result: LocationData = {
                    "id": location.id,
                    "name": location.name,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "country": location.country,
                    "region": location.region,
                }

                logger.info(f"Location saved or found: {name} (ID: {location.id})")
                return result

            except Exception as e:
                logger.error(f"Error finding or creating location: {e}")
                # Fall back to the coordinates only if there's an error
                return {"lat": latitude, "lon": longitude}

        except Exception as e:
            logger.error(f"Error saving location to database: {e}")
            # Return just the coordinates without ID if there was an error
            lat_value = location_data.get("lat", 0)
            lon_value = location_data.get("lon", 0)
            return {"lat": float(lat_value), "lon": float(lon_value)}

    def get_favorite_locations(self) -> list[Location]:
        """
        Get all favorite locations from the database

        Returns:
            List of favorite Location objects
        """
        return self.location_repo.get_favorites()

    def toggle_favorite(self, location_id: int) -> bool:
        """
        Toggle the favorite status of a location

        Args:
            location_id: ID of the location to toggle

        Returns:
            True if successful, False otherwise
        """
        try:
            location: Optional[Location] = self.location_repo.get_by_id(location_id)
            if location:
                # Toggle the favorite status
                new_favorite_status: bool = not location.is_favorite
                updated: Optional[Location] = self.location_repo.update(
                    location_id, {"is_favorite": new_favorite_status}
                )
                return updated is not None
            return False
        except Exception as e:
            logger.error(f"Error toggling favorite status: {e}")
            return False
