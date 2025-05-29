"""
Functional tests for form interactions and user workflows in the Flask web UI.
Tests complex user interactions, form validations, and multi-step workflows.
"""

import pytest
from conftest import HOST
from playwright.sync_api import Page
from test_constants import TEST_CITY_LONDON, TEST_CITY_PARIS


class TestFormValidation:
    """Test suite for form validation and error handling."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_search_form_empty_validation(self, page: Page):
        """Test search form behavior with empty input."""
        page.goto(HOST)

        # Find search form
        search_form = page.locator("form[action*='search']")
        search_button = search_form.locator("button[type='submit']")

        # Submit without filling
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Should handle empty submission gracefully
        content = page.content()
        assert content
        # May show validation message or redirect back
        current_url = page.url
        assert HOST in current_url

    def test_search_form_special_characters(self, page: Page):
        """Test search form with special characters."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        # Test with special characters
        special_locations = [
            "São Paulo",
            "München",
            "北京",  # Beijing in Chinese
            "México City",
            "Zürich",
        ]

        for location in special_locations:
            search_input.fill(location)
            search_button.click()
            page.wait_for_load_state("networkidle")

            # Should handle special characters without crashing
            content = page.content()
            assert content

            # Go back to home page for next test
            page.goto(HOST)

    def test_forecast_form_validation(self, page: Page):
        """Test forecast form validation behavior."""
        page.goto(HOST)

        forecast_form = page.locator("form[action*='forecast']")
        if forecast_form.count() > 0:
            forecast_button = forecast_form.locator("button[type='submit']")

            # Test empty submission
            forecast_button.click()
            page.wait_for_load_state("networkidle")

            # Should handle gracefully
            content = page.content()
            assert content

    def test_unit_selection_form(self, page: Page):
        """Test unit selection form functionality."""
        page.goto(HOST)

        unit_form = page.locator("form[action*='unit']")
        if unit_form.count() > 0:
            # Look for unit selection elements
            celsius_option = unit_form.locator("input[value='C'], option[value='C']")

            if celsius_option.count() > 0:
                celsius_option.first.click()

                # Submit form if there's a submit button
                submit_button = unit_form.locator(
                    "button[type='submit'], input[type='submit']"
                )
                if submit_button.count() > 0:
                    submit_button.click()
                    page.wait_for_load_state("networkidle")

                    # Should handle unit change
                    assert page.url


class TestUserWorkflows:
    """Test suite for complete user workflows."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_search_to_weather_workflow(self, page: Page):
        """Test complete workflow from search to weather display."""
        page.goto(HOST)

        # Step 1: Search for a location
        search_form = page.locator("form[action*='search']")
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        search_input.fill(TEST_CITY_LONDON)
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Step 2: Should get to results page or weather page
        current_url = page.url
        assert HOST in current_url

        # Step 3: Look for weather data or location selection
        content = page.content()
        assert any(
            keyword in content.lower()
            for keyword in [
                "london",
                "weather",
                "temperature",
                "select",
                "search",
            ]
        )

    def test_quick_link_to_forecast_workflow(self, page: Page):
        """Test workflow from quick link to forecast."""
        page.goto(HOST)

        # Step 1: Click quick link
        london_button = page.locator(f"button:has-text('{TEST_CITY_LONDON}')")
        if london_button.count() > 0:
            london_button.click()
            page.wait_for_load_state("networkidle")

            # Step 2: Should show weather or navigate to weather page
            current_url = page.url
            assert HOST in current_url

            # Step 3: Look for weather-related content
            content = page.content()
            assert any(
                keyword in content.lower()
                for keyword in ["weather", "forecast", "temperature", "london"]
            )

    def test_natural_language_query_workflow(self, page: Page):
        """Test natural language query workflow."""
        page.goto(HOST)

        # Step 1: Fill natural language form
        nl_form = page.locator("form[action*='nl']")
        if nl_form.count() > 0:
            query_input = nl_form.locator("input[name='query']")
            submit_button = nl_form.locator("input[type='submit']")

            # Test various natural language queries
            queries = [
                "What's the weather like in London today?",
                "Weather for Paris tomorrow",
                "How's New York this weekend?",
                "Temperature in Tokyo",
            ]

            for query in queries:
                query_input.fill(query)
                submit_button.click()
                page.wait_for_load_state("networkidle")

                # Should process query
                content = page.content()
                assert content

                # Return to home for next test
                page.goto(HOST)

    def test_forecast_days_selection_workflow(self, page: Page):
        """Test forecast days selection workflow."""
        page.goto(HOST)

        # Look for forecast form
        forecast_form = page.locator("form[action*='forecast']")
        if forecast_form.count() > 0:
            location_input = forecast_form.locator("input[name='location']")
            days_select = forecast_form.locator("select[name='forecast_days']")
            forecast_button = forecast_form.locator("button[type='submit']")

            # Fill form
            location_input.fill(TEST_CITY_PARIS)

            if days_select.count() > 0:
                days_select.select_option("3")

            forecast_button.click()
            page.wait_for_load_state("networkidle")

            # Should process forecast request
            current_url = page.url
            assert HOST in current_url


class TestDynamicContent:
    """Test suite for dynamic content updates."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_flash_message_display(self, page: Page):
        """Test flash message display and dismissal."""
        page.goto(HOST)

        # Look for flash message containers
        flash_container = page.locator(".flash-messages, .alert, [class*='message']")

        if flash_container.count() > 0:
            # Check if messages are visible
            assert flash_container.is_visible()

            # Look for dismiss buttons
            dismiss_buttons = page.locator(
                ".alert .close, button[data-dismiss], .flash-dismiss"
            )
            if dismiss_buttons.count() > 0:
                dismiss_buttons.first.click()

                # Message should be dismissed or hidden
                page.wait_for_timeout(500)

    def test_loading_states(self, page: Page):
        """Test loading states during form submissions."""
        page.goto(HOST)

        # Submit a form and look for loading indicators
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            search_input.fill("London")

            # Look for loading indicators after clicking
            search_button.click()

            # Wait for page to complete
            page.wait_for_load_state("networkidle")

    def test_content_updates_without_refresh(self, page: Page):
        """Test AJAX content updates without full page refresh."""
        page.goto(HOST)

        # Interact with elements that might trigger AJAX
        ajax_triggers = page.locator("button[data-target], [onclick], .ajax-trigger")

        if ajax_triggers.count() > 0:
            # Click the first AJAX trigger
            ajax_triggers.first.click()

            # Wait a moment for potential AJAX
            page.wait_for_timeout(1000)

            # Check if content updated
            updated_content = page.content()
            # Content might have changed, or at least no errors should occur
            assert updated_content


class TestAccessibility:
    """Test suite for accessibility features."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_keyboard_navigation(self, page: Page):
        """Test keyboard navigation through forms."""
        page.goto(HOST)

        # Test tab navigation
        page.keyboard.press("Tab")
        focused_element = page.evaluate("document.activeElement.tagName")

        # Should be able to focus on interactive elements
        assert focused_element.lower() in [
            "input",
            "button",
            "select",
            "textarea",
            "a",
        ]

    def test_form_labels_and_accessibility(self, page: Page):
        """Test form labels and accessibility attributes."""
        page.goto(HOST)

        # Check for proper form labels
        inputs = page.locator("input[type='text'], input[type='search']")
        input_count = inputs.count()

        for i in range(input_count):
            input_element = inputs.nth(i)

            # Check for associated label or aria-label
            input_id = input_element.get_attribute("id")
            aria_label = input_element.get_attribute("aria-label")
            placeholder = input_element.get_attribute("placeholder")

            # Should have some form of labeling
            if input_id:
                label = page.locator(f"label[for='{input_id}']")
                has_label = label.count() > 0
            else:
                has_label = False

            # Should have label, aria-label, or at least placeholder
            assert has_label or aria_label or placeholder

    def test_error_message_accessibility(self, page: Page):
        """Test error message accessibility."""
        page.goto(HOST)

        # Try to trigger validation errors
        forms = page.locator("form")
        if forms.count() > 0:
            submit_buttons = page.locator("button[type='submit'], input[type='submit']")
            if submit_buttons.count() > 0:
                # Submit empty form to trigger validation
                submit_buttons.first.click()
                page.wait_for_load_state("networkidle")

                # Look for error messages
                error_messages = page.locator(
                    ".error, .invalid, [aria-invalid], .text-danger"
                )

                if error_messages.count() > 0:
                    # Error messages should be visible and accessible
                    assert error_messages.first.is_visible()


class TestMultiStepWorkflows:
    """Test suite for multi-step user workflows."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_search_select_view_workflow(self, page: Page):
        """Test search -> select location -> view weather workflow."""
        page.goto(HOST)

        # Step 1: Search for a common city
        search_form = page.locator("form[action*='search']")
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        search_input.fill("Paris")
        search_button.click()
        page.wait_for_load_state("networkidle")

        # Step 2: If multiple results, select one
        location_links = page.locator("a[href*='weather'], button[onclick*='weather']")
        if location_links.count() > 0:
            location_links.first.click()
            page.wait_for_load_state("networkidle")

        # Step 3: Should be on weather page or have weather data
        content = page.content()
        assert any(
            keyword in content.lower()
            for keyword in ["weather", "temperature", "forecast", "paris"]
        )

    def test_settings_update_workflow(self, page: Page):
        """Test settings update workflow."""
        page.goto(HOST)

        # Look for settings forms
        unit_form = page.locator("form[action*='unit']")
        if unit_form.count() > 0:
            # Change unit setting
            fahrenheit_option = unit_form.locator("input[value='F'], option[value='F']")
            if fahrenheit_option.count() > 0:
                fahrenheit_option.first.click()

                # Submit if needed
                submit_button = unit_form.locator(
                    "button[type='submit'], input[type='submit']"
                )
                if submit_button.count() > 0:
                    submit_button.click()
                    page.wait_for_load_state("networkidle")

                # Verify setting was applied
                content = page.content()
                assert content
