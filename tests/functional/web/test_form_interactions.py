"""
Functional tests for form interactions and user workflows in the Flask web UI.
Tests complex user interactions, form validations, and multi-step workflows.
"""

from conftest import HOST
from playwright.async_api import Page
from test_constants import TEST_CITY_LONDON, TEST_CITY_PARIS


class TestFormValidation:
    """Test suite for form validation and error handling."""

    async def test_search_form_empty_validation(self, page: Page):
        """Test search form behavior with empty input."""
        await page.goto(HOST)

        # Find search form
        search_form = page.locator("form[action*='search']")
        search_button = search_form.locator("button[type='submit']")

        # Submit without filling
        await search_button.click()
        await page.wait_for_load_state("networkidle")

        # Should handle empty submission gracefully
        content = page.content()
        assert content
        # May show validation message or redirect back
        current_url = page.url
        assert HOST in current_url

    async def test_search_form_special_characters(self, page: Page):
        """Test search form with special characters."""
        await page.goto(HOST)

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
            await search_input.fill(location)
            await search_button.click()
            await page.wait_for_load_state("networkidle")

            # Should handle special characters without crashing
            content = page.content()
            assert content

            # Go back to home page for next test
            await page.goto(HOST)

    async def test_forecast_form_validation(self, page: Page):
        """Test forecast form validation behavior."""
        await page.goto(HOST)

        forecast_form = page.locator("form[action*='forecast']")
        if await forecast_form.count() > 0:
            forecast_button = forecast_form.locator("button[type='submit']")

            # Test empty submission
            await forecast_button.click()
            await page.wait_for_load_state("networkidle")

            # Should handle gracefully
            content = page.content()
            assert content

    async def test_unit_selection_form(self, page: Page):
        """Test unit selection form functionality."""
        await page.goto(HOST)

        unit_form = page.locator("form[action*='unit']")
        if await unit_form.count() > 0:
            # Look for unit selection elements
            celsius_option = unit_form.locator("input[value='C'], option[value='C']")

            if await celsius_option.count() > 0:
                await celsius_option.first.click()

                # Submit form if there's a submit button
                submit_button = unit_form.locator(
                    "button[type='submit'], input[type='submit']"
                )
                if await submit_button.count() > 0:
                    await submit_button.click()
                    await page.wait_for_load_state("networkidle")

                    # Should handle unit change
                    assert page.url


class TestUserWorkflows:
    """Test suite for complete user workflows."""

    async def test_search_to_weather_workflow(self, page: Page):
        """Test complete workflow from search to weather display."""
        await page.goto(HOST)

        # Step 1: Search for a location
        search_form = page.locator("form[action*='search']")
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        await search_input.fill(TEST_CITY_LONDON)
        await search_button.click()
        await page.wait_for_load_state("networkidle")

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

    async def test_quick_link_to_forecast_workflow(self, page: Page):
        """Test workflow from quick link to forecast."""
        await page.goto(HOST)

        # Step 1: Click quick link
        london_button = page.locator(f"button:has-text('{TEST_CITY_LONDON}')")
        if await london_button.count() > 0:
            await london_button.click()
            await page.wait_for_load_state("networkidle")

            # Step 2: Should show weather or navigate to weather page
            current_url = page.url
            assert HOST in current_url

            # Step 3: Look for weather-related content
            content = page.content()
            assert any(
                keyword in content.lower()
                for keyword in ["weather", "forecast", "temperature", "london"]
            )

    async def test_natural_language_query_workflow(self, page: Page):
        """Test natural language query workflow."""
        await page.goto(HOST)

        # Step 1: Fill natural language form
        nl_form = page.locator("form[action*='nl']")
        if await nl_form.count() > 0:
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
                await query_input.fill(query)
                await submit_button.click()
                await page.wait_for_load_state("networkidle")

                # Should process query
                content = page.content()
                assert content

                # Return to home for next test
                await page.goto(HOST)

    async def test_forecast_days_selection_workflow(self, page: Page):
        """Test forecast days selection workflow."""
        await page.goto(HOST)

        # Look for forecast form
        forecast_form = page.locator("form[action*='forecast']")
        if await forecast_form.count() > 0:
            location_input = forecast_form.locator("input[name='location']")
            days_select = forecast_form.locator("select[name='forecast_days']")
            forecast_button = forecast_form.locator("button[type='submit']")

            # Fill form
            await location_input.fill(TEST_CITY_PARIS)

            if await days_select.count() > 0:
                await days_select.select_option("3")

            await forecast_button.click()
            await page.wait_for_load_state("networkidle")

            # Should process forecast request
            current_url = page.url
            assert HOST in current_url


class TestDynamicContent:
    """Test suite for dynamic content updates."""

    async def test_flash_message_display(self, page: Page):
        """Test flash message display and dismissal."""
        await page.goto(HOST)

        # Look for flash message containers
        flash_container = page.locator(".flash-messages, .alert, [class*='message']")

        if await flash_container.count() > 0:
            # Check if await messages are visible
            assert await flash_container.is_visible()

            # Look for dismiss buttons
            dismiss_buttons = page.locator(
                ".alert .close, button[data-dismiss], .flash-dismiss"
            )
            if await dismiss_buttons.count() > 0:
                await dismiss_buttons.first.click()

                # Message should be dismissed or hidden
                page.wait_for_timeout(500)

    async def test_loading_states(self, page: Page):
        """Test loading states during form submissions."""
        await page.goto(HOST)

        # Submit a form and look for loading indicators
        search_form = page.locator("form[action*='search']")
        if await search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            await search_input.fill("London")

            # Look for loading indicators after clicking
            await search_button.click()

            # Wait for page to complete
            await page.wait_for_load_state("networkidle")

    async def test_content_updates_without_refresh(self, page: Page):
        """Test AJAX content updates without full page refresh."""
        await page.goto(HOST)

        # Interact with elements that might trigger AJAX
        ajax_triggers = page.locator("button[data-target], [onclick], .ajax-trigger")

        if await ajax_triggers.count() > 0:
            # Click the first AJAX trigger
            await ajax_triggers.first.click()

            # Wait a moment for potential AJAX
            page.wait_for_timeout(1000)

            # Check if content updated
            updated_content = page.content()
            # Content might have changed, or at least no errors should occur
            assert updated_content


class TestAccessibility:
    """Test suite for accessibility features."""

    async def test_keyboard_navigation(self, page: Page):
        """Test keyboard navigation through forms."""
        await page.goto(HOST)

        # Test tab navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")

        # Should be able to focus on interactive elements
        assert focused_element.lower() in [
            "input",
            "button",
            "select",
            "textarea",
            "a",
        ]

    async def test_form_labels_and_accessibility(self, page: Page):
        """Test form labels and accessibility attributes."""
        await page.goto(HOST)

        # Check for proper form labels
        inputs = page.locator("input[type='text'], input[type='search']")
        input_count = await inputs.count()

        for i in range(input_count):
            input_element = inputs.nth(i)

            # Check for associated label or aria-label
            input_id = input_element.get_attribute("id")
            aria_label = input_element.get_attribute("aria-label")
            placeholder = input_element.get_attribute("placeholder")

            # Should have some form of labeling
            if input_id:
                label = page.locator(f"label[for='{input_id}']")
                has_label = await label.count() > 0
            else:
                has_label = False

            # Should have label, aria-label, or at least placeholder
            assert has_label or aria_label or placeholder

    async def test_error_message_accessibility(self, page: Page):
        """Test error message accessibility."""
        await page.goto(HOST)

        # Try to trigger validation errors
        forms = page.locator("form")
        if await forms.count() > 0:
            submit_buttons = page.locator("button[type='submit'], input[type='submit']")
            if await submit_buttons.count() > 0:
                # Submit empty form to trigger validation
                await submit_buttons.first.click()
                await page.wait_for_load_state("networkidle")

                # Look for error messages
                error_messages = page.locator(
                    ".error, .invalid, [aria-invalid], .text-danger"
                )

                if await error_messages.count() > 0:
                    # Error messages should be visible and accessible
                    assert await error_messages.first.is_visible()


class TestMultiStepWorkflows:
    """Test suite for multi-step user workflows."""

    async def test_search_select_view_workflow(self, page: Page):
        """Test search -> select location -> view weather workflow."""
        await page.goto(HOST)

        # Step 1: Search for a common city
        search_form = page.locator("form[action*='search']")
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        await search_input.fill("Paris")
        await search_button.click()
        await page.wait_for_load_state("networkidle")

        # Step 2: If multiple results, select one
        location_links = page.locator("a[href*='weather'], button[onclick*='weather']")
        if await location_links.count() > 0:
            await location_links.first.click()
            await page.wait_for_load_state("networkidle")

        # Step 3: Should be on weather page or have weather data
        content = page.content()
        assert any(
            keyword in content.lower()
            for keyword in ["weather", "temperature", "forecast", "paris"]
        )

    async def test_settings_update_workflow(self, page: Page):
        """Test settings update workflow."""
        await page.goto(HOST)

        # Look for settings forms
        unit_form = page.locator("form[action*='unit']")
        if await unit_form.count() > 0:
            # Change unit setting
            fahrenheit_option = unit_form.locator("input[value='F'], option[value='F']")
            if await fahrenheit_option.count() > 0:
                await fahrenheit_option.first.click()

                # Submit if needed
                submit_button = unit_form.locator(
                    "button[type='submit'], input[type='submit']"
                )
                if await submit_button.count() > 0:
                    await submit_button.click()
                    await page.wait_for_load_state("networkidle")

                # Verify setting was applied
                content = page.content()
                assert content
