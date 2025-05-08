import logging

logger = logging.getLogger("weather_app")


class User_Input_Information:
    @staticmethod
    def get_search_query() -> str:
        search_query = input(
            "Search for a location (city, region, etc.) or 'q' to go back: "
        ).strip()
        logger.debug(f"User entered search query: {search_query}")
        return search_query

    @staticmethod
    def get_location_selection(city_count: int) -> str:
        return input(f"Select a location (1-{city_count}) or 'q' to search again: ")

    @staticmethod
    def get_location_method() -> str:
        print("\nHow would you like to select a location?")
        print("1. Search for a location")
        print("2. Enter location directly")
        print("3. Use saved location")
        print("q. Quit")
        choice = input("Enter your choice (1-3 or q): ")
        logger.debug(f"User selected location method: {choice}")
        return choice

    @staticmethod
    def get_direct_location() -> str:
        location = input(
            "Enter location (city, region, etc.) or 'q' to go back: "
        ).strip()
        logger.debug(f"User entered direct location: {location}")
        return location

    @staticmethod
    def confirm_verified_locations() -> str:
        return input("\nUse one of these locations? (y/n): ").lower()

    @staticmethod
    def get_verified_location_selection(locations_count: int) -> str:
        return input(f"Select a location (1-{locations_count}) or 'q' to cancel: ")

    @staticmethod
    def confirm_retry() -> str:
        return input("Would you like to try again? (y/n): ").lower()

    @staticmethod
    def get_temperature_choice() -> str:
        """Ask user to choose temperature unit"""
        print("\nSelect temperature unit:")
        print("1. Celsius (°C)")
        print("2. Fahrenheit (°F)")
        choice = input("Enter choice (1 or 2): ").strip()
        logger.debug(f"User selected temperature unit: {choice}")
        return choice
