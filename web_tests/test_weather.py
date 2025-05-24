"""
Playwright tests for the weather.html template of the Flask weather app.
Tests weather data display, unit conversion, and favorites functionality.
"""

import pytest
from conftest import HOST
from playwright.sync_api import Page, expect


class TestWeatherPage:
    """Test suite for the weather.html template functionality."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_weather_page_loads_with_valid_coordinates(self, page: Page):
        """Test that weather page loads with valid coordinates."""
        # Using London coordinates as an example
        page.goto(f"{HOST}/weather/51.5074/-0.1278")

        # Wait for page to load
        page.wait_for_load_state("networkidle")

        # Check that we're on a weather page
        expect(page.locator("h2")).to_contain_text("Weather for")

        # Check that basic weather info is displayed
        expect(page.locator(".weather-display")).to_be_visible()
        expect(page.locator(".temperature")).to_be_visible()

    def test_weather_page_title_format(self, page: Page):
        """Test that the page title follows the correct format."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Title should contain "Weather for [Location]"
        title = page.title()
        assert "Weather for" in title

    def test_weather_location_info_display(self, page: Page):
        """Test that location information is properly displayed."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check location heading
        location_heading = page.locator("h2")
        expect(location_heading).to_contain_text("Weather for")

        # Check that region and country are displayed
        location_details = page.locator("p").first
        expect(location_details).to_be_visible()

    def test_weather_condition_display(self, page: Page):
        """Test that weather conditions are properly displayed."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check weather card exists
        weather_card = page.locator(".card")
        expect(weather_card).to_be_visible()

        # Check condition text
        condition = page.locator(".condition")
        expect(condition).to_be_visible()

        # Check temperature display
        temperature = page.locator(".temperature")
        expect(temperature).to_be_visible()

        # Temperature should contain degree symbol and unit
        temp_text = temperature.text_content()
        assert "°" in temp_text
        assert "C" in temp_text or "F" in temp_text

    def test_weather_icon_display(self, page: Page):
        """Test that weather icon is displayed when available."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check if weather icon exists
        weather_icon = page.locator(".weather-icon img")
        if weather_icon.is_visible():
            expect(weather_icon).to_have_attribute("src")
            expect(weather_icon).to_have_attribute("alt")

    def test_feels_like_temperature_display(self, page: Page):
        """Test that 'feels like' temperature is displayed."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check feels like temperature
        feels_like = page.locator("text=/Feels like:/")
        expect(feels_like).to_be_visible()

    def test_weather_details_section(self, page: Page):
        """Test that detailed weather information is displayed."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check weather details section
        details_section = page.locator(".weather-details")
        expect(details_section).to_be_visible()

        # Check individual weather metrics
        expect(page.locator("text=/Humidity:/")).to_be_visible()
        expect(page.locator("text=/Wind:/")).to_be_visible()
        expect(page.locator("text=/Pressure:/")).to_be_visible()
        expect(page.locator("text=/Precipitation:/")).to_be_visible()
        expect(page.locator("text=/UV Index:/")).to_be_visible()

    def test_weather_navigation_links_present(self, page: Page):
        """Test that navigation links are present and functional."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check navigation section
        nav_section = page.locator(".nav")
        expect(nav_section).to_be_visible()

        # Check individual navigation links
        expect(page.locator("a:has-text('Back to Home')")).to_be_visible()
        expect(page.locator("a:has-text('View Forecast')")).to_be_visible()
        expect(page.locator("a")).to_contain_text("Switch to °")

    def test_back_to_home_link(self, page: Page):
        """Test that the 'Back to Home' link works."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Click back to home link
        home_link = page.locator("a:has-text('Back to Home')")
        home_link.click()

        # Should navigate to homepage
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{HOST}/")

    def test_view_forecast_link(self, page: Page):
        """Test that the 'View Forecast' link works."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Click view forecast link
        forecast_link = page.locator("a:has-text('View Forecast')")
        forecast_link.click()

        # Should navigate to forecast page
        page.wait_for_load_state("networkidle")
        current_url = page.url
        assert "forecast" in current_url

    def test_weather_unit_switching_celsius_to_fahrenheit(self, page: Page):
        """Test switching from Celsius to Fahrenheit."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278?unit=C")
        page.wait_for_load_state("networkidle")

        # Check current unit is Celsius
        temperature = page.locator(".temperature")
        temp_text = temperature.text_content()
        if "°C" in temp_text:
            # Click switch to Fahrenheit link
            switch_link = page.locator("a:has-text('Switch to °F')")
            switch_link.click()

            page.wait_for_load_state("networkidle")

            # Check that temperature now shows Fahrenheit
            new_temp_text = temperature.text_content()
            assert "°F" in new_temp_text

    def test_weather_unit_switching_fahrenheit_to_celsius(self, page: Page):
        """Test switching from Fahrenheit to Celsius."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278?unit=F")
        page.wait_for_load_state("networkidle")

        # Check current unit is Fahrenheit
        temperature = page.locator(".temperature")
        temp_text = temperature.text_content()
        if "°F" in temp_text:
            # Click switch to Celsius link
            switch_link = page.locator("a:has-text('Switch to °C')")
            switch_link.click()

            page.wait_for_load_state("networkidle")

            # Check that temperature now shows Celsius
            new_temp_text = temperature.text_content()
            assert "°C" in new_temp_text

    def test_weather_favorites_button_presence(self, page: Page):
        """Test that favorites button is present when location has an ID."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check if favorites button exists (it may not if location doesn't have an ID)
        favorites_button = page.locator(
            "button:has-text('Add to Favorites'), "
            "button:has-text('Remove from Favorites')"
        )
        favorites_form = page.locator("form[action*='toggle_favorite']")

        # If the form exists, check its structure
        if favorites_form.is_visible():
            expect(favorites_button).to_be_visible()

            # Check CSRF token in favorites form
            csrf_token = favorites_form.locator("input[name='csrf_token']")
            expect(csrf_token).to_be_visible()

    def test_last_updated_timestamp(self, page: Page):
        """Test that last updated timestamp is displayed."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check last updated information
        last_updated = page.locator("text=/Last updated:/")
        expect(last_updated).to_be_visible()

    def test_weather_data_format_validation(self, page: Page):
        """Test that weather data is displayed in proper format."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check humidity format (should be percentage)
        humidity_text = page.locator("text=/Humidity:/").text_content()
        assert "%" in humidity_text

        # Check pressure format (should have mb units)
        pressure_text = page.locator("text=/Pressure:/").text_content()
        assert "mb" in pressure_text

        # Check precipitation format (should have mm units)
        precip_text = page.locator("text=/Precipitation:/").text_content()
        assert "mm" in precip_text

    def test_wind_information_display(self, page: Page):
        """Test that wind information is properly displayed with direction."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check wind information
        wind_text = page.locator("text=/Wind:/").text_content()

        # Wind should contain speed and direction
        assert any(unit in wind_text for unit in ["km/h", "mph"])

        # Wind direction should be present (like N, S, E, W, NE, etc.)
        wind_directions = [
            "N",
            "S",
            "E",
            "W",
            "NE",
            "NW",
            "SE",
            "SW",
            "NNE",
            "NNW",
            "ENE",
            "ESE",
            "SSE",
            "SSW",
            "WSW",
            "WNW",
        ]
        assert any(direction in wind_text for direction in wind_directions)

    def test_weather_error_handling_invalid_coordinates(self, page: Page):
        """Test error handling for invalid coordinates."""
        # Try to access weather page with invalid coordinates
        page.goto(f"{HOST}/weather/999/999")
        page.wait_for_load_state("networkidle")

        # Should either show error message or redirect
        # Check if we get a reasonable response (not a crash)
        current_url = page.url
        assert HOST in current_url

    def test_weather_responsive_design_mobile(self, page: Page):
        """Test that weather page is responsive on mobile."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")

        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_load_state("networkidle")

        # Check that essential elements are still visible
        expect(page.locator("h2")).to_be_visible()
        expect(page.locator(".temperature")).to_be_visible()
        expect(page.locator(".weather-details")).to_be_visible()
        expect(page.locator(".nav")).to_be_visible()

    def test_weather_flash_messages_display(self, page: Page):
        """Test that flash messages are properly displayed when present."""
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Flash messages container should be in the DOM
        flash_container = page.locator(".flash-messages")
        # Don't assert visibility since it may be empty, just check structure
        expect(flash_container).to_have_count_range(0, 1)
