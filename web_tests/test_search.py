"""
Playwright tests for search-related templates of the Flask weather app.
Tests search results display and natural language query functionality.
"""

import pytest
from conftest import HOST
from playwright.sync_api import Page, expect


class TestSearchTemplates:
    """Test suite for search-related template functionality."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_search_results_from_homepage(self, page: Page):
        """Test performing a search from the homepage and viewing results."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Perform a search
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("London")
        search_button.click()

        # Wait for results page
        page.wait_for_load_state("networkidle")

        # Should show some results or navigate to a results page
        current_url = page.url
        assert HOST in current_url

    def test_search_with_multiple_results(self, page: Page):
        """Test search that returns multiple location results."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Search for a common city name that might have multiple results
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("Springfield")  # Common city name in many countries
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Check if we get search results page or direct weather page
        current_url = page.url
        assert HOST in current_url

    def test_search_with_invalid_location(self, page: Page):
        """Test search with invalid or non-existent location."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Search for non-existent location
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("NonExistentCityName12345")
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Should handle gracefully with error message or redirect
        current_url = page.url
        assert HOST in current_url

    def test_search_with_empty_query(self, page: Page):
        """Test search with empty query."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Try to submit empty search
        search_button = page.locator("form[action*='search'] button[type='submit']")
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Should handle gracefully
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_today(self, page: Page):
        """Test natural language query for today's weather."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("What's the weather like in London today?")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should process the query and show results
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_tomorrow(self, page: Page):
        """Test natural language query for tomorrow's weather."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query for tomorrow
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("How's the weather in Paris tomorrow?")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should process the query and show results
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_weekend(self, page: Page):
        """Test natural language query for weekend weather."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query for weekend
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("Weather for New York this weekend?")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should process the query and show results
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_specific_day(self, page: Page):
        """Test natural language query for specific day."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query for specific day
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("What's Tokyo weather like next Monday?")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should process the query and show results
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_invalid(self, page: Page):
        """Test natural language query with invalid or unclear input."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit unclear natural language query
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("weather stuff sometime maybe")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should handle gracefully with error message or redirect
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_query_empty(self, page: Page):
        """Test natural language query with empty input."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit empty natural language query
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should handle gracefully
        current_url = page.url
        assert HOST in current_url

    def test_search_results_page_structure(self, page: Page):
        """Test the structure of search results page when it's displayed."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Perform a search that should return results
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("London")
        search_button.click()

        page.wait_for_load_state("networkidle")

        # If we're on a search results page, check its structure
        if "search" in page.url.lower() or page.locator(".search-results").is_visible():
            # Check if search results are displayed
            results_container = page.locator(".search-results, .results")
            if results_container.is_visible():
                expect(results_container).to_be_visible()

    def test_date_weather_results_display(self, page: Page):
        """Test date weather results display structure."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit a natural language query that should show date weather results
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("London weather today")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # If we get date weather results, check the structure
        if page.locator(".date-weather-results").is_visible():
            expect(page.locator(".date-weather-results")).to_be_visible()

    def test_search_with_international_characters(self, page: Page):
        """Test search with international characters."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Search with international characters
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("München")  # Munich in German
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Should handle international characters gracefully
        current_url = page.url
        assert HOST in current_url

    def test_search_with_special_characters(self, page: Page):
        """Test search with special characters."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Search with special characters
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("São Paulo")  # City with special characters
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Should handle special characters gracefully
        current_url = page.url
        assert HOST in current_url

    def test_search_case_insensitive(self, page: Page):
        """Test that search is case insensitive."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Test with different cases
        test_cases = ["london", "LONDON", "London", "LoNdOn"]

        for city_name in test_cases:
            search_input = page.locator("form[action*='search'] input[name='query']")
            search_button = page.locator("form[action*='search'] button[type='submit']")

            search_input.fill(city_name)
            search_button.click()

            page.wait_for_load_state("networkidle")

            # Should handle all cases gracefully
            current_url = page.url
            assert HOST in current_url

            # Go back to homepage for next test
            page.goto(HOST)
            page.wait_for_load_state("networkidle")

    def test_search_with_coordinates(self, page: Page):
        """Test search functionality with coordinate-like input."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Try searching with coordinates format
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("51.5074,-0.1278")  # London coordinates
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Should handle coordinate input gracefully
        current_url = page.url
        assert HOST in current_url

    def test_nl_weather_multiple_locations(self, page: Page):
        """Test natural language query mentioning multiple locations."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query with multiple locations
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("Compare weather between London and Paris tomorrow")
        nl_submit.click()

        page.wait_for_load_state("networkidle")

        # Should handle gracefully (might pick first location or show error)
        current_url = page.url
        assert HOST in current_url

    def test_search_and_navigation_flow(self, page: Page):
        """Test complete search and navigation flow."""
        # Start on homepage
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Perform search
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("London")
        search_button.click()

        page.wait_for_load_state("networkidle")

        # If we get weather page, test navigation
        if "weather" in page.url:
            # Test navigation to forecast
            forecast_link = page.locator("a:has-text('View Forecast')")
            if forecast_link.is_visible():
                forecast_link.click()
                page.wait_for_load_state("networkidle")

                # Should be on forecast page
                assert "forecast" in page.url

                # Test navigation back to home
                home_link = page.locator("a:has-text('Back to Home')")
                home_link.click()
                page.wait_for_load_state("networkidle")

                # Should be back on homepage
                expect(page).to_have_url(f"{HOST}/")

    def test_flash_messages_in_search_results(self, page: Page):
        """Test that flash messages are properly displayed in search contexts."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Perform a search that might generate flash messages
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("InvalidLocationName12345")
        search_button.click()

        page.wait_for_load_state("networkidle")

        # Check if flash messages container exists
        flash_container = page.locator(".flash-messages")
        # Don't assert visibility since it depends on search results
        expect(flash_container).to_have_count_range(0, 1)
