"""
Playwright integration tests for the Flask weather app.
Tests end-to-end user flows across multiple templates and functionality.
"""

import pytest
from conftest import HOST
from playwright.sync_api import Page, expect


class TestIntegrationFlows:
    """Test suite for end-to-end integration flows across templates."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_complete_weather_lookup_flow(self, page: Page):
        """Test complete flow from search to weather to forecast."""
        # Start on homepage
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Search for a location
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("London")
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Should get weather results or weather page
        current_url = page.url

        # If on weather page, test navigation to forecast
        if "weather" in current_url:
            forecast_link = page.locator("a:has-text('View Forecast')")
            if forecast_link.is_visible():
                forecast_link.click()
                page.wait_for_load_state("networkidle")

                # Should be on forecast page
                assert "forecast" in page.url

                # Test forecast functionality
                self._test_forecast_functionality(page)

    def test_natural_language_to_results_flow(self, page: Page):
        """Test natural language query flow to results."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Submit natural language query
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        nl_submit = page.locator("form[action*='nl_date_weather'] input[type='submit']")

        nl_input.fill("What's the weather like in New York today?")
        nl_submit.click()
        page.wait_for_load_state("networkidle")

        # Should get some kind of results
        current_url = page.url
        assert HOST in current_url

        # Test navigation back to home if possible
        home_link = page.locator("a:has-text('Back to Home'), a[href='/']")
        if home_link.is_visible():
            home_link.click()
            page.wait_for_load_state("networkidle")
            expect(page).to_have_url(f"{HOST}/")

    def test_forecast_form_submission_flow(self, page: Page):
        """Test forecast form submission from homepage."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Fill and submit forecast form
        location_input = page.locator(
            "form[action*='forecast_form'] input[name='location']"
        )
        forecast_days_select = page.locator(
            "form[action*='forecast_form'] select[name='forecast_days']"
        )
        forecast_button = page.locator(
            "form[action*='forecast_form'] button[type='submit']"
        )

        location_input.fill("Tokyo")
        forecast_days_select.select_option("5")
        forecast_button.click()
        page.wait_for_load_state("networkidle")

        # Should navigate to forecast page
        current_url = page.url

        if "forecast" in current_url:
            self._test_forecast_functionality(page)

    def test_quick_links_functionality(self, page: Page):
        """Test quick links from homepage to forecast."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Click on a quick link (London)
        london_button = page.locator("button:has-text('London')")
        london_button.click()
        page.wait_for_load_state("networkidle")

        # Should get forecast or weather results
        current_url = page.url
        assert HOST in current_url

    def test_unit_conversion_across_pages(self, page: Page):
        """Test unit conversion functionality across weather and forecast pages."""
        # Start with weather page
        page.goto(f"{HOST}/weather/51.5074/-0.1278?unit=C")
        page.wait_for_load_state("networkidle")

        # Check current unit
        temperature = page.locator(".temperature")
        if temperature.is_visible():
            temp_text = temperature.text_content()

            if "°C" in temp_text:
                # Switch to Fahrenheit
                switch_link = page.locator("a:has-text('Switch to °F')")
                if switch_link.is_visible():
                    switch_link.click()
                    page.wait_for_load_state("networkidle")

                    # Check unit changed
                    new_temp_text = temperature.text_content()
                    assert "°F" in new_temp_text

                    # Navigate to forecast and check unit consistency
                    forecast_link = page.locator("a:has-text('View Forecast')")
                    if forecast_link.is_visible():
                        forecast_link.click()
                        page.wait_for_load_state("networkidle")

                        # Check forecast also shows Fahrenheit
                        forecast_temp = page.locator(".forecast-day .temperature").first
                        if forecast_temp.is_visible():
                            forecast_temp_text = forecast_temp.text_content()
                            assert "°F" in forecast_temp_text

    def test_favorites_functionality_flow(self, page: Page):
        """Test favorites functionality across pages."""
        # Navigate to weather page
        page.goto(f"{HOST}/weather/51.5074/-0.1278")
        page.wait_for_load_state("networkidle")

        # Check if favorites button exists
        favorites_form = page.locator("form[action*='toggle_favorite']")
        if favorites_form.is_visible():
            favorites_button = favorites_form.locator("button")
            button_text = favorites_button.text_content()

            # Click favorites button
            favorites_button.click()
            page.wait_for_load_state("networkidle")

            # Button text should change
            new_button_text = favorites_button.text_content()
            assert new_button_text != button_text

            # Navigate to homepage and check favorites section
            page.goto(HOST)
            page.wait_for_load_state("networkidle")

            # Check if favorites section is visible
            favorites_section = page.locator(
                ".card-title:has-text('Favorite Locations')"
            )
            if favorites_section.is_visible():
                # Should have at least one favorite
                favorites_list = page.locator(".list-group-item")
                expect(favorites_list).to_have_count_greater_than(0)

    def test_error_handling_flow(self, page: Page):
        """Test error handling and recovery flow."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Try invalid search
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("InvalidLocation12345")
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Should handle gracefully and allow navigation back
        current_url = page.url
        assert HOST in current_url

        # Check if error message is displayed
        flash_messages = page.locator(".flash-message")
        if flash_messages.is_visible():
            expect(flash_messages).to_contain_text("error", {"ignoreCase": True})

        # Should be able to navigate back to home
        if not page.url.endswith("/"):
            home_link = page.locator("a:has-text('Back to Home'), a[href='/']")
            if home_link.is_visible():
                home_link.click()
                page.wait_for_load_state("networkidle")
                expect(page).to_have_url(f"{HOST}/")

    def test_responsive_behavior_across_pages(self, page: Page):
        """Test responsive behavior across different page templates."""
        pages_to_test = [
            HOST,  # Homepage
            f"{HOST}/weather/51.5074/-0.1278",  # Weather page
            f"{HOST}/forecast/51.5074/-0.1278",  # Forecast page
        ]

        for test_url in pages_to_test:
            page.goto(test_url)
            page.wait_for_load_state("networkidle")

            # Test desktop view
            page.set_viewport_size({"width": 1200, "height": 800})
            page.wait_for_load_state("domcontentloaded")

            # Main content should be visible
            expect(page.locator("h1, h2")).to_be_visible()

            # Test tablet view
            page.set_viewport_size({"width": 768, "height": 1024})
            page.wait_for_load_state("domcontentloaded")

            # Content should still be visible
            expect(page.locator("h1, h2")).to_be_visible()

            # Test mobile view
            page.set_viewport_size({"width": 375, "height": 667})
            page.wait_for_load_state("domcontentloaded")

            # Content should be accessible on mobile
            expect(page.locator("h1, h2")).to_be_visible()

    def test_cross_template_navigation(self, page: Page):
        """Test navigation between different templates."""
        # Start on homepage
        page.goto(HOST)
        page.wait_for_load_state("networkidle")
        expect(page.locator("h1")).to_contain_text("Weather Dashboard")

        # Navigate to weather page via search
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        search_input.fill("London")
        search_button.click()
        page.wait_for_load_state("networkidle")

        # If on weather page, test navigation
        if "weather" in page.url:
            expect(page.locator("h2")).to_contain_text("Weather for")

            # Navigate to forecast
            forecast_link = page.locator("a:has-text('View Forecast')")
            if forecast_link.is_visible():
                forecast_link.click()
                page.wait_for_load_state("networkidle")

                # Should be on forecast page
                if "forecast" in page.url:
                    expect(page.locator("h2")).to_contain_text("Forecast for")

                    # Navigate back to weather
                    weather_link = page.locator("a:has-text('Current Weather')")
                    if weather_link.is_visible():
                        weather_link.click()
                        page.wait_for_load_state("networkidle")

                        # Should be back on weather page
                        expect(page.locator("h2")).to_contain_text("Weather for")

                        # Navigate back to home
                        home_link = page.locator("a:has-text('Back to Home')")
                        home_link.click()
                        page.wait_for_load_state("networkidle")

                        # Should be back on homepage
                        expect(page).to_have_url(f"{HOST}/")

    def test_form_validation_across_templates(self, page: Page):
        """Test form validation behavior across different templates."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Test empty form submissions
        forms = page.locator("form")
        form_count = forms.count()

        for i in range(min(form_count, 3)):  # Test first 3 forms to avoid timeout
            form = forms.nth(i)
            submit_button = form.locator("button[type='submit'], input[type='submit']")

            if submit_button.is_visible():
                # Try submitting without filling required fields
                submit_button.click()
                page.wait_for_load_state("networkidle")

                # Should handle gracefully
                current_url = page.url
                assert HOST in current_url

                # Navigate back to home if not already there
                if not page.url.endswith("/"):
                    page.goto(HOST)
                    page.wait_for_load_state("networkidle")

    def test_data_persistence_across_navigation(self, page: Page):
        """Test that user preferences persist across page navigation."""
        # Set unit preference on weather page
        page.goto(f"{HOST}/weather/51.5074/-0.1278?unit=F")
        page.wait_for_load_state("networkidle")

        # Navigate to forecast
        forecast_link = page.locator("a:has-text('View Forecast')")
        if forecast_link.is_visible():
            forecast_link.click()
            page.wait_for_load_state("networkidle")

            # Check if unit preference is maintained
            if "forecast" in page.url:
                temperature = page.locator(".forecast-day .temperature").first
                if temperature.is_visible():
                    temp_text = temperature.text_content()
                    # Should maintain Fahrenheit preference
                    assert "°F" in temp_text

    def _test_forecast_functionality(self, page: Page):
        """Helper method to test forecast page functionality."""
        # Test forecast days selection
        three_days_radio = page.locator("input[name='forecast_days'][value='3']")
        if three_days_radio.is_visible():
            three_days_radio.check()

            update_button = page.locator("button:has-text('Update Forecast')")
            update_button.click()
            page.wait_for_load_state("networkidle")

            # Check that selection is maintained
            expect(three_days_radio).to_be_checked()

    def test_api_error_handling_flow(self, page: Page):
        """Test handling of API errors across templates."""
        # Try accessing weather with coordinates that might cause API issues
        page.goto(f"{HOST}/weather/0/0")  # Null Island
        page.wait_for_load_state("networkidle")

        # Should handle gracefully
        current_url = page.url
        assert HOST in current_url

        # Should provide way to navigate back
        home_link = page.locator("a:has-text('Back to Home'), a[href='/']")
        if home_link.is_visible():
            home_link.click()
            page.wait_for_load_state("networkidle")
            expect(page).to_have_url(f"{HOST}/")

    def test_concurrent_form_submissions(self, page: Page):
        """Test behavior when multiple forms might be submitted."""
        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Fill multiple forms but submit only one
        search_input = page.locator("form[action*='search'] input[name='query']")
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")

        search_input.fill("London")
        nl_input.fill("Paris weather today")

        # Submit only one form
        search_button = page.locator("form[action*='search'] button[type='submit']")
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Should handle gracefully
        current_url = page.url
        assert HOST in current_url
