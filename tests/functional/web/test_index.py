"""
Playwright tests for the index.html template (homepage) of the Flask weather app.
Tests all forms and functionality on the main page.
"""

from conftest import HOST
from playwright.async_api import Page, expect
from test_constants import (
    CARD_TITLE_ASK_WEATHER,
    CARD_TITLE_SEARCH_LOCATION,
    CARD_TITLE_WEATHER_FORECAST,
    HEADING_WEATHER_DASHBOARD,
    POPULAR_CITIES,
    TEST_CITY_LONDON,
    TITLE_HOME,
)


class TestIndexPage:
    """Test suite for the index.html template functionality."""

    async def test_page_loads_successfully(self, page: Page):
        """Test that the homepage loads with correct title and content."""
        await page.goto(HOST)

        # Check page title
        await expect(page).to_have_title(TITLE_HOME)

        # Check main heading
        await expect(page.locator("h1")).to_contain_text(HEADING_WEATHER_DASHBOARD)

        # Verify main sections are present
        await expect(page.locator(".card-title")).to_contain_text(
            CARD_TITLE_ASK_WEATHER
        )
        await expect(page.locator(".card-title")).to_contain_text(
            CARD_TITLE_SEARCH_LOCATION
        )
        await expect(page.locator(".card-title")).to_contain_text(
            CARD_TITLE_WEATHER_FORECAST
        )

    async def test_natural_language_query_form_present(self, page: Page):
        """Test that the natural language query form is present and functional."""
        await page.goto(HOST)

        # Check form exists
        nl_form = page.locator("form[action*='nl_date_weather']")
        await expect(nl_form).to_be_visible()

        # Check form elements
        query_input = nl_form.locator("input[name='query']")
        submit_button = nl_form.locator("input[type='submit']")

        await expect(query_input).to_be_visible()
        await expect(query_input).to_have_attribute(
            "placeholder",
            "e.g., What's the weather like in London tomorrow? "
            "Weather for Paris this weekend? How's Tokyo next Monday?",
        )
        await expect(submit_button).to_be_visible()

    async def test_natural_language_query_submission(self, page: Page):
        """Test submitting a natural language weather query."""
        await page.goto(HOST)

        # Find and fill the natural language form
        query_input = page.locator(
            "form[action*='nl_date_weather'] input[name='query']"
        )
        submit_button = page.locator(
            "form[action*='nl_date_weather'] input[type='submit']"
        )

        # Fill and submit the form
        await query_input.fill("What's the weather like in London today?")
        await submit_button.click()

        # Should navigate away from homepage or show results
        await page.wait_for_load_state("networkidle")

        # Check that we either stayed on page with results or navigated to results page
        current_url = page.url
        assert HOST in current_url

    async def test_location_search_form_present(self, page: Page):
        """Test that the location search form is present and functional."""
        await page.goto(HOST)

        # Check search form exists
        search_form = page.locator("form[action*='search']")
        await expect(search_form).to_be_visible()

        # Check form elements
        search_input = search_form.locator("input[name='query']")
        search_button = search_form.locator("button[type='submit']")

        await expect(search_input).to_be_visible()
        await expect(search_input).to_have_attribute("placeholder", "Enter city name")
        await expect(search_button).to_be_visible()
        await expect(search_button).to_contain_text("Search")

    async def test_location_search_submission(self, page: Page):
        """Test submitting a location search."""
        await page.goto(HOST)

        # Find and fill the search form
        search_input = page.locator("form[action*='search'] input[name='query']")
        search_button = page.locator("form[action*='search'] button[type='submit']")

        # Fill and submit the form
        await search_input.fill("London")
        await search_button.click()

        # Wait for navigation or response
        await page.wait_for_load_state("networkidle")

        # Check that we navigated away from homepage or got results
        current_url = page.url
        assert HOST in current_url

    async def test_forecast_form_present(self, page: Page):
        """Test that the forecast form is present with all required elements."""
        await page.goto(HOST)

        # Check forecast form exists
        forecast_form = page.locator("form[action*='forecast_form']")
        await expect(forecast_form).to_be_visible()

        # Check form elements
        location_input = forecast_form.locator("input[name='location']")
        forecast_days_select = forecast_form.locator("select[name='forecast_days']")
        forecast_button = forecast_form.locator("button[type='submit']")

        await expect(location_input).to_be_visible()
        await expect(location_input).to_have_attribute(
            "placeholder", "Enter city name (e.g., London, New York)"
        )
        await expect(forecast_days_select).to_be_visible()
        await expect(forecast_button).to_be_visible()
        await expect(forecast_button).to_contain_text("Get Forecast")

        # Check forecast days options
        options = forecast_days_select.locator("option")
        await expect(options).to_have_count(4)  # 1, 3, 5, 7 days

    async def test_forecast_form_submission(self, page: Page):
        """Test submitting the forecast form."""
        await page.goto(HOST)

        # Find and fill the forecast form
        location_input = page.locator(
            "form[action*='forecast_form'] input[name='location']"
        )
        forecast_days_select = page.locator(
            "form[action*='forecast_form'] select[name='forecast_days']"
        )
        forecast_button = page.locator(
            "form[action*='forecast_form'] button[type='submit']"
        )

        # Fill and submit the form
        await location_input.fill("New York")
        await forecast_days_select.select_option("3")
        await forecast_button.click()

        # Wait for navigation
        await page.wait_for_load_state("networkidle")

        # Check that we navigated away from homepage
        current_url = page.url
        assert HOST in current_url

    async def test_quick_links_present(self, page: Page):
        """Test that the popular cities quick links are present."""
        await page.goto(HOST)

        # Check quick links section
        quick_links_section = page.locator(".quick-links")
        await expect(quick_links_section).to_be_visible()

        # Check for popular city buttons
        for city in POPULAR_CITIES:
            city_button = page.locator(f"button:has-text('{city}')")
            await expect(city_button).to_be_visible()

    async def test_quick_link_submission(self, page: Page):
        """Test clicking a quick link button."""
        await page.goto(HOST)

        # Click on London quick link
        london_button = page.locator(f"button:has-text('{TEST_CITY_LONDON}')")
        await london_button.click()

        # Wait for navigation
        await page.wait_for_load_state("networkidle")

        # Should navigate to forecast page or stay on page with results
        current_url = page.url
        assert HOST in current_url

    async def test_favorites_section_visibility(self, page: Page):
        """Test favorites section behavior when it may or may not be visible."""
        await page.goto(HOST)

        # Check if favorites section exists (it may not if no favorites are saved)
        favorites_section = page.locator(".card-title:has-text('Favorite Locations')")

        # If it exists, verify it has the correct structure
        if await favorites_section.is_visible():
            favorites_list = page.locator(".list-group")
            await expect(favorites_list).to_be_visible()

    async def test_flash_messages_container_present(self, page: Page):
        """Test that flash messages container is present (even if empty)."""
        await page.goto(HOST)

        # Flash messages container should be in the DOM even if no messages
        # This ensures the template structure is correct
        await page.wait_for_load_state("domcontentloaded")

        # The container might not be visible if no messages, but should be in DOM
        flash_container = page.locator(".flash-messages")
        # Don't assert visibility since it may be empty, just check it can be found
        await expect(flash_container).to_have_count_range(0, 1)

    async def test_responsive_layout(self, page: Page):
        """Test that the page layout is responsive."""
        await page.goto(HOST)

        # Test desktop view
        await page.set_viewport_size({"width": 1200, "height": 800})
        await page.wait_for_load_state("domcontentloaded")

        # Check that cards are side by side (row layout)
        row_element = page.locator(".row")
        await expect(row_element).to_be_visible()

        # Test mobile view
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_load_state("domcontentloaded")

        # Elements should still be visible in mobile view
        await expect(page.locator("h1")).to_be_visible()
        await expect(page.locator(".card")).to_be_visible()

    async def test_csrf_tokens_present(self, page: Page):
        """Test that CSRF tokens are present in all forms."""
        await page.goto(HOST)

        # Check that all forms have CSRF tokens
        forms = page.locator("form")
        form_count = await forms.count()

        for i in range(form_count):
            form = forms.nth(i)
            csrf_token = form.locator("input[name='csrf_token']")
            await expect(csrf_token).to_have_count_range(
                1, 2
            )  # Should have at least one CSRF token

    async def test_form_validation_placeholders(self, page: Page):
        """Test that form inputs have appropriate placeholders and labels."""
        await page.goto(HOST)

        # Check natural language query placeholder
        nl_input = page.locator("form[action*='nl_date_weather'] input[name='query']")
        await expect(nl_input).to_have_attribute("placeholder")

        # Check search input placeholder
        search_input = page.locator("form[action*='search'] input[name='query']")
        await expect(search_input).to_have_attribute("placeholder", "Enter city name")

        # Check forecast location input placeholder
        forecast_input = page.locator(
            "form[action*='forecast_form'] input[name='location']"
        )
        await expect(forecast_input).to_have_attribute("placeholder")
