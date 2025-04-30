import logging

logger = logging.getLogger("weather_app")


class User_Input_Information:
    @staticmethod
    def get_search_query() -> str:
        search_query = input("Search for a location (city, region, etc.): ").strip()
        logger.debug(f"User entered search query: {search_query}")
        return search_query

    @staticmethod
    def get_location_selection(city_count: int) -> str:
        return input(f"Select a location (1-{city_count}) or 'q' to search again: ")

    @staticmethod
    def get_location_method() -> str:
        print("\n1. Search for a location\n2. Enter location directly")
        return input("Enter your choice (1-2): ")

    @staticmethod
    def get_direct_location() -> str:
        return input("Enter location: ").strip()

    @staticmethod
    def confirm_verified_locations() -> str:
        return input("\nUse one of these locations? (y/n): ").lower()

    @staticmethod
    def get_verified_location_selection(locations_count: int) -> str:
        return input(f"Select a location (1-{locations_count}) or 'q' to cancel: ")

    @staticmethod
    def confirm_retry() -> str:
        return input("Would you like to try again? (y/n): ").lower()

    # @staticmethod
    # def get_temperature_choice() -> str:
    #     """Ask user to choose temperature unit"""
    #     print("\nSelect temperature unit:")
    #     print("1. Celsius (°C)")
    #     print("2. Fahrenheit (°F)")
    #     choice = input("Enter choice (1 or 2): ").strip()
    #     return choice
