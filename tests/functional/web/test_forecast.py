"""
Playwright tests for the forecast.html template of the Flask weather app.
Tests forecast data display, forecast days selection, and related functionality.
"""

from conftest import HOST
from playwright.async_api import Page, expect


class TestForecastPage:
    """Test suite for the forecast.html template functionality."""

    async def test_forecast_page_loads_with_valid_coordinates(self, page: Page):
        """Test that forecast page loads with valid coordinates."""
        # Using London coordinates as an example
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")

        # Wait for page to load
        await page.wait_for_load_state("networkidle")

        # Check that we're on a forecast page
        await expect(page.locator("h2")).to_contain_text("Forecast for")

        # Check that forecast container is displayed
        await expect(page.locator(".weather-display")).to_be_visible()

    async def test_forecast_page_title_format(self, page: Page):
        """Test that the page title follows the correct format."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Title should contain "Weather Forecast for [Location]"
        title = await page.title()
        assert "Weather Forecast for" in title

    async def test_forecast_location_info_display(self, page: Page):
        """Test that location information is properly displayed."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check forecast heading with location
        location_heading = page.locator("h2")
        await expect(location_heading).to_contain_text("Forecast for")

        # Check that region and country are displayed
        location_details = page.locator("p").first
        await expect(location_details).to_be_visible()

    async def test_forecast_days_form_present(self, page: Page):
        """Test that the forecast days selection form is present."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check forecast days form exists
        forecast_form = page.locator(".forecast-days-form form")
        await expect(forecast_form).to_be_visible()

        # Check radio buttons for different day options
        await expect(
            page.locator("input[name='forecast_days'][value='1']")
        ).to_be_visible()
        await expect(
            page.locator("input[name='forecast_days'][value='3']")
        ).to_be_visible()
        await expect(
            page.locator("input[name='forecast_days'][value='5']")
        ).to_be_visible()
        await expect(
            page.locator("input[name='forecast_days'][value='7']")
        ).to_be_visible()

        # Check update button
        await expect(page.locator("button:has-text('Update Forecast')")).to_be_visible()

    async def test_forecast_days_labels(self, page: Page):
        """Test that forecast days labels are properly displayed."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check labels for each forecast day option
        await expect(page.locator("label[for='days1']")).to_contain_text("1 Day")
        await expect(page.locator("label[for='days3']")).to_contain_text("3 Days")
        await expect(page.locator("label[for='days5']")).to_contain_text("5 Days")
        await expect(page.locator("label[for='days7']")).to_contain_text("7 Days")

    async def test_forecast_days_selection_change(self, page: Page):
        """Test changing the forecast days selection."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Select 3 days forecast
        three_days_radio = page.locator("input[name='forecast_days'][value='3']")
        await three_days_radio.check()

        # Click update button
        update_button = page.locator("button:has-text('Update Forecast')")
        await update_button.click()

        # Wait for page to update
        await page.wait_for_load_state("networkidle")

        # Check that 3 days option is selected
        await expect(three_days_radio).to_be_checked()

    async def test_forecast_container_present(self, page: Page):
        """Test that the forecast container with days is displayed."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check forecast container exists
        forecast_container = page.locator(".forecast-container")
        await expect(forecast_container).to_be_visible()

        # Check that forecast days are present
        forecast_days = page.locator(".forecast-day")
        await expect(forecast_days).to_have_count_greater_than(0)

    async def test_individual_forecast_day_structure(self, page: Page):
        """Test the structure of individual forecast day cards."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check first forecast day structure
        first_day = page.locator(".forecast-day").first
        await expect(first_day).to_be_visible()

        # Check date heading
        await expect(first_day.locator("h3")).to_be_visible()

        # Check condition display
        await expect(first_day.locator(".condition")).to_be_visible()

        # Check temperature display
        await expect(first_day.locator(".temperature")).to_be_visible()

        # Check forecast details
        await expect(first_day.locator(".forecast-details")).to_be_visible()

    async def test_forecast_temperature_format(self, page: Page):
        """Test that temperatures are displayed in correct format."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check temperature format in first forecast day
        temperature_element = page.locator(".forecast-day .temperature").first
        temp_text = await temperature_element.text_content()

        # Should contain max and min temperatures with degree symbol
        assert "°" in temp_text
        assert "/" in temp_text  # Separator between max and min
        assert "C" in temp_text or "F" in temp_text

    async def test_forecast_weather_details(self, page: Page):
        """Test that detailed weather information is displayed for each day."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check first forecast day details
        first_day_details = page.locator(".forecast-day .forecast-details").first

        # Check individual weather metrics
        await expect(first_day_details.locator("text=/Humidity:/")).to_be_visible()
        await expect(first_day_details.locator("text=/Wind:/")).to_be_visible()
        await expect(first_day_details.locator("text=/Rain Chance:/")).to_be_visible()
        await expect(first_day_details.locator("text=/Snow Chance:/")).to_be_visible()

    async def test_forecast_weather_icons(self, page: Page):
        """Test that weather icons are displayed for await forecast days."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check if weather icons exist
        forecast_icons = page.locator(".forecast-icon img")

        # If icons are present, they should have proper attributes
        if await forecast_icons.first.is_visible():
            await expect(forecast_icons.first).to_have_attribute("src")
            await expect(forecast_icons.first).to_have_attribute("alt")

    async def test_forecast_navigation_links_present(self, page: Page):
        """Test that navigation links are present and functional."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check navigation section
        nav_section = page.locator(".nav")
        await expect(nav_section).to_be_visible()

        # Check individual navigation links
        await expect(page.locator("a:has-text('Back to Home')")).to_be_visible()
        await expect(page.locator("a:has-text('Current Weather')")).to_be_visible()
        await expect(page.locator("a")).to_contain_text("Switch to °")

    async def test_forecast_back_to_home_navigation(self, page: Page):
        """Test that the 'Back to Home' link works."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Click back to home link
        home_link = page.locator("a:has-text('Back to Home')")
        await home_link.click()

        # Should navigate to homepage
        await page.wait_for_load_state("networkidle")
        await expect(page).to_have_url(f"{HOST}/")

    async def test_forecast_current_weather_navigation(self, page: Page):
        """Test that the 'Current Weather' link works."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Click current weather link
        weather_link = page.locator("a:has-text('Current Weather')")
        await weather_link.click()

        # Should navigate to weather page
        await page.wait_for_load_state("networkidle")
        current_url = page.url
        assert "weather" in current_url

    async def test_forecast_unit_switching_celsius_to_fahrenheit(self, page: Page):
        """Test switching from Celsius to Fahrenheit."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278?unit=C")
        await page.wait_for_load_state("networkidle")

        # Check current unit is Celsius
        temperature = page.locator(".forecast-day .temperature").first
        temp_text = await temperature.text_content()
        if "°C" in temp_text:
            # Click switch to Fahrenheit link
            switch_link = page.locator("a:has-text('Switch to °F')")
            await switch_link.click()

            await page.wait_for_load_state("networkidle")

            # Check that temperature now shows Fahrenheit
            new_temp_text = await temperature.text_content()
            assert "°F" in new_temp_text

    async def test_forecast_unit_switching_fahrenheit_to_celsius(self, page: Page):
        """Test switching from Fahrenheit to Celsius."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278?unit=F")
        await page.wait_for_load_state("networkidle")

        # Check current unit is Fahrenheit
        temperature = page.locator(".forecast-day .temperature").first
        temp_text = await temperature.text_content()
        if "°F" in temp_text:
            # Click switch to Celsius link
            switch_link = page.locator("a:has-text('Switch to °C')")
            await switch_link.click()

            await page.wait_for_load_state("networkidle")

            # Check that temperature now shows Celsius
            new_temp_text = await temperature.text_content()
            assert "°C" in new_temp_text

    async def test_forecast_favorites_button_presence(self, page: Page):
        """Test that favorites button is present when location has an ID."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check if favorites button exists
        favorites_button = page.locator(
            "button:has-text('Add to Favorites'), "
            "button:has-text('Remove from Favorites')"
        )
        favorites_form = page.locator("form[action*='toggle_favorite']")

        # If the form exists, check its structure
        if await favorites_form.is_visible():
            await expect(favorites_button).to_be_visible()

            # Check CSRF token in favorites form
            csrf_token = favorites_form.locator("input[name='csrf_token']")
            await expect(csrf_token).to_be_visible()

    async def test_forecast_data_format_validation(self, page: Page):
        """Test that forecast data is displayed in proper format."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check first forecast day details
        first_day = page.locator(".forecast-day").first

        # Check humidity format (should be percentage)
        humidity_text = await first_day.locator("text=/Humidity:/").text_content()
        assert "%" in humidity_text

        # Check rain chance format (should be percentage)
        rain_text = await first_day.locator("text=/Rain Chance:/").text_content()
        assert "%" in rain_text

        # Check snow chance format (should be percentage)
        snow_text = await first_day.locator("text=/Snow Chance:/").text_content()
        assert "%" in snow_text

    async def test_forecast_wind_information_in_forecast(self, page: Page):
        """Test that wind information is properly displayed in forecast."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check wind information in first forecast day
        wind_element = page.locator(".forecast-day .forecast-details").first.locator(
            "text=/Wind:/"
        )
        wind_text = await wind_element.text_content()

        # Wind should contain speed units
        assert any(unit in wind_text for unit in ["km/h", "mph", "kph"])

    async def test_forecast_date_format_in_forecast(self, page: Page):
        """Test that dates are properly formatted in forecast days."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check that dates are displayed
        date_headers = page.locator(".forecast-day h3")
        await expect(date_headers.first).to_be_visible()

        # Date text should not be empty
        date_text = await date_headers.first.text_content()
        assert len(date_text.strip()) > 0

    async def test_forecast_responsive_design_mobile(self, page: Page):
        """Test that forecast page is responsive on mobile."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")

        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_load_state("networkidle")

        # Check that essential elements are still visible
        await expect(page.locator("h2")).to_be_visible()
        await expect(page.locator(".forecast-container")).to_be_visible()
        await expect(page.locator(".forecast-day")).to_be_visible()
        await expect(page.locator(".nav")).to_be_visible()

    async def test_forecast_csrf_token_in_forecast_form(self, page: Page):
        """Test that CSRF token is present in forecast days form."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Check CSRF token in forecast days form
        forecast_form = page.locator(".forecast-days-form form")
        csrf_token = forecast_form.locator("input[name='csrf_token']")
        await expect(csrf_token).to_be_visible()

    async def test_forecast_error_handling_invalid_coordinates(self, page: Page):
        """Test error handling for invalid coordinates."""
        # Try to access forecast page with invalid coordinates
        await page.goto(f"{HOST}/forecast/999/999")
        await page.wait_for_load_state("networkidle")

        # Should either show error message or redirect
        # Check if we get a reasonable response (not a crash)
        current_url = page.url
        assert HOST in current_url

    async def test_forecast_flash_messages_display(self, page: Page):
        """Test that flash messages are properly displayed when present."""
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Flash messages container should be in the DOM
        flash_container = page.locator(".flash-messages")
        # Don't assert visibility since it may be empty, just check structure
        await expect(flash_container).to_have_count_range(0, 1)

    async def test_forecast_with_different_day_counts(self, page: Page):
        """Test that forecast displays different numbers of days correctly."""
        # Test 1 day forecast
        await page.goto(f"{HOST}/forecast/51.5074/-0.1278")
        await page.wait_for_load_state("networkidle")

        # Select 1 day
        one_day_radio = page.locator("input[name='forecast_days'][value='1']")
        await one_day_radio.check()

        # Update forecast
        update_button = page.locator("button:has-text('Update Forecast')")
        await update_button.click()
        await page.wait_for_load_state("networkidle")

        # Check that 1 day is selected
        await expect(one_day_radio).to_be_checked()

        # Test 7 days forecast
        seven_days_radio = page.locator("input[name='forecast_days'][value='7']")
        await seven_days_radio.check()
        await update_button.click()
        await page.wait_for_load_state("networkidle")

        # Check that 7 days is selected
        await expect(seven_days_radio).to_be_checked()
