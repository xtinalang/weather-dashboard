import logging
from typing import Optional, cast

from .api import WeatherAPI
from .database import init_db
from .display import WeatherDisplay
from .models import Location
from .repository import LocationRepository
from .user_input import User_Input_Information
from .weather_types import LocationData

logger = logging.getLogger("weather_app")

# Module-level instances for reuse
_weather_api: Optional[WeatherAPI] = None
_display: Optional[WeatherDisplay] = None
_user_input: Optional[User_Input_Information] = None
_location_repo: Optional[LocationRepository] = None


def _get_weather_api() -> WeatherAPI:
    """Get or create WeatherAPI instance"""
    global _weather_api
    if _weather_api is None:
        _weather_api = WeatherAPI()
    return _weather_api


def _get_display() -> WeatherDisplay:
    """Get or create WeatherDisplay instance"""
    global _display
    if _display is None:
        _display = WeatherDisplay()
    return _display


def _get_user_input() -> User_Input_Information:
    """Get or create User_Input_Information instance"""
    global _user_input
    if _user_input is None:
        _user_input = User_Input_Information()
    return _user_input


def _get_location_repo() -> LocationRepository:
    """Get or create LocationRepository instance"""
    global _location_repo
    if _location_repo is None:
        _location_repo = LocationRepository()
    return _location_repo


def check_database() -> None:
    """Check if database is initialized, initialize if needed"""
    try:
        # Try to count locations
        location_repo = _get_location_repo()
        count: int = location_repo.count()
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


def search_location() -> str | None:
    """Search for a location via API"""
    max_attempts: int = 3
    weather_api = _get_weather_api()
    display = _get_display()
    user_input = _get_user_input()

    for _ in range(max_attempts):
        try:
            query: str = user_input.get_search_query()
            if not query:
                continue

            logger.debug(f"Searching for location: {query}")
            city_list: list[LocationData] | None = cast(
                list[LocationData] | None, weather_api.search_city(query)
            )

            if not city_list:
                logger.warning(f"No results found for query: {query}")
                print(
                    f"No cities found matching '{query}'. Please try a different search term."
                )
                continue

            display.show_city(city_list)
            selection: str = user_input.get_location_selection(len(city_list))

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
                    location_info: LocationData = save_location_to_db(selected)
                    if "id" in location_info:
                        logger.debug(f"Location saved with ID: {location_info['id']}")

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


def direct_location() -> str | None:
    """Get location directly from user input"""
    max_attempts: int = 3
    weather_api = _get_weather_api()
    display = _get_display()
    user_input = _get_user_input()

    for _ in range(max_attempts):
        try:
            location: str = user_input.get_direct_location()
            if not location:
                continue

            logger.debug(f"Searching for direct location: {location}")
            results: list[LocationData] | None = cast(
                list[LocationData] | None, weather_api.search_city(location)
            )

            if not results:
                logger.warning(f"No results found for direct location: {location}")
                print(
                    f"No cities found matching '{location}'. Please try a different location."
                )
                continue

            display.show_city(results)

            # Ask user to confirm
            print("\nIs this the correct location? (y/n)")
            confirm: str = input("> ").lower()
            if confirm != "y":
                continue

            # Save the first result to the database
            location_info: LocationData = save_location_to_db(results[0])
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


def use_saved_location() -> str | None:
    """Use a previously saved location"""
    try:
        location_repo = _get_location_repo()
        # Get favorite locations first
        favorites: list[Location] = location_repo.get_favorites()

        # If no favorites, get all locations
        locations: list[Location]
        if not favorites:
            locations = location_repo.get_all(limit=10)
        else:
            locations = favorites

        if not locations:
            print("No saved locations found. Please search for a location first.")
            return search_location()

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
        return use_saved_location()
    except Exception as e:
        logger.error(f"Error getting saved locations: {e}")
        print(f"Error retrieving saved locations: {e}")
        return None


def save_location_to_db(location_data: LocationData) -> LocationData:
    """Save location data to database"""
    try:
        location_repo = _get_location_repo()
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
            location: Location = location_repo.find_or_create_by_coordinates(
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


def get_favorite_locations() -> list[Location]:
    """Get all favorite locations"""
    location_repo = _get_location_repo()
    return location_repo.get_favorites()


def toggle_favorite(location_id: int) -> bool:
    """Toggle favorite status of a location"""
    try:
        location_repo = _get_location_repo()
        location: Optional[Location] = location_repo.get_by_id(location_id)
        if location:
            # Toggle the favorite status
            new_favorite_status: bool = not location.is_favorite
            updated: Optional[Location] = location_repo.update(
                location_id, {"is_favorite": new_favorite_status}
            )
            return updated is not None
        return False
    except Exception as e:
        logger.error(f"Error toggling favorite status: {e}")
        return False


def get_coordinates(location_name: str) -> Optional[tuple[float, float]] | None:
    """Get coordinates for a location"""
    try:
        location_repo = _get_location_repo()
        weather_api = _get_weather_api()

        # First try to find by name in database
        location: Optional[Location] = location_repo.find_by_name(location_name)
        if location:
            return location.latitude, location.longitude

        # If not found, try to find by region
        location: Optional[Location] = location_repo.find_by_region(location_name)
        if location:
            return location.latitude, location.longitude

        # If not found, try to find by country
        location: Optional[Location] = location_repo.find_by_country(location_name)
        if location:
            return location.latitude, location.longitude

        # If not found in database, try API search
        try:
            results = weather_api.search_city(location_name)
            if results and len(results) > 0:
                # Use the first result
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])

                # Create and save new location
                new_location = Location(
                    name=results[0]["name"],
                    region=results[0].get("region", ""),
                    country=results[0].get("country", ""),
                    latitude=lat,
                    longitude=lon,
                )
                location_repo.save(new_location)

                return lat, lon
        except Exception as api_error:
            logger.error(f"API search failed for {location_name}: {api_error}")

        # If all searches fail, return None
        return None

    except Exception as e:
        logger.error(f"Error getting coordinates for {location_name}: {e}")
        return None


def get_location() -> str | None:
    """Main function to get location from user"""
    try:
        # Check if database is initialized and has locations
        check_database()
        user_input = _get_user_input()

        while True:
            method: str = user_input.get_location_method()
            if method == "1":
                return search_location()
            elif method == "2":
                return direct_location()
            elif method == "3":  # Add an option to use saved locations
                return use_saved_location()
            elif method.lower() == "q":
                return None
    except Exception as e:
        logger.error(f"Error in get_location: {e}")
        display = _get_display()
        display.show_error(f"Error retrieving location: {e}")
        return None


# Backwards compatibility: Keep LocationManager class for existing code
class LocationManager:
    """Backwards compatibility wrapper around the flattened functions"""

    def __init__(self, weather_api: WeatherAPI, display: WeatherDisplay) -> None:
        # Initialize global instances with provided objects
        global _weather_api, _display
        _weather_api = weather_api
        _display = display

    def get_location(self) -> str | None:
        return get_location()

    def get_favorite_locations(self) -> list[Location]:
        return get_favorite_locations()

    def toggle_favorite(self, location_id: int) -> bool:
        return toggle_favorite(location_id)

    def get_coordinates(self, location_name: str) -> Optional[tuple[float, float]]:
        return get_coordinates(location_name)
