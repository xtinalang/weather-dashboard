"""
Health check and core functionality tests for the Weather Dashboard.
"""

from playwright.async_api import Page, expect

# Update this to match your application's host and port
HOST = "http://localhost:5001"


async def test_homepage_loads(page: Page):
    """Test that the homepage loads and contains essential elements."""
    response = await page.goto(HOST)
    assert response and response.ok, "Homepage failed to load"

    # Check main components
    await expect(page).to_have_title("Weather Dashboard")
    await expect(page.locator("form[action*='search']")).to_be_visible()
    await expect(page.locator("input[name='query']")).to_be_visible()
    await expect(page.locator("button[type='submit']")).to_be_visible()


async def test_search_functionality(page: Page):
    """Test the search functionality with a known city."""
    await page.goto(HOST)

    # Fill and submit the search form
    search_input = page.locator("input[name='query']")
    search_button = page.locator("form[action*='search'] button[type='submit']")

    await search_input.fill("London")
    await search_button.click()

    # Wait for navigation and check results
    await page.wait_for_load_state("networkidle")

    # We should either see weather results or location selection
    success = (
        await page.locator(".weather-data").is_visible()
        or await page.locator(".location-selection").is_visible()
    )
    assert success, "Search results not displayed"


async def test_natural_language_query(page: Page):
    """Test the natural language weather query functionality."""
    await page.goto(HOST)

    # Find and fill the NL query form
    nl_input = page.locator("input[name='query']").nth(1)  # Second query input on page
    nl_button = page.locator("form[action*='nl-date-weather'] button[type='submit']")

    await nl_input.fill("What's the weather like in London tomorrow?")
    await nl_button.click()

    # Wait for navigation and check results
    await page.wait_for_load_state("networkidle")

    # Should see either weather results or location selection
    success = (
        await page.locator(".weather-data").is_visible()
        or await page.locator(".location-selection").is_visible()
    )
    assert success, "Natural language query results not displayed"


async def test_unit_toggle(page: Page):
    """Test temperature unit toggle functionality."""
    await page.goto(HOST)

    # Find and click unit toggle
    unit_form = page.locator("form[action*='unit']")
    unit_options = unit_form.locator("input[name='unit']")

    # Try to change unit
    if await unit_options.nth(1).is_visible():
        await unit_options.nth(1).click()
        await unit_form.locator("button[type='submit']").click()

        # Wait for reload
        await page.wait_for_load_state("networkidle")

        # Verify the change was saved
        assert page.url == HOST, "Unit change should redirect to homepage"


async def test_forecast_days(page: Page):
    """Test forecast days selection functionality."""
    await page.goto(HOST)

    # Find and change forecast days
    forecast_form = page.locator("form[action*='forecast']")
    forecast_select = forecast_form.locator("select[name='forecast_days']")

    if await forecast_select.is_visible():
        # Select a different value
        await forecast_select.select_option("5")
        await forecast_form.locator("button[type='submit']").click()

        # Wait for reload
        await page.wait_for_load_state("networkidle")

        # Verify we're back on homepage
        assert page.url == HOST, "Forecast days change should redirect to homepage"


async def test_error_handling(page: Page):
    """Test error handling with invalid input."""
    await page.goto(HOST)

    # Try invalid search
    search_input = page.locator("input[name='query']")
    search_button = page.locator("form[action*='search'] button[type='submit']")

    await search_input.fill("!@#$%")
    await search_button.click()

    # Wait for navigation
    await page.wait_for_load_state("networkidle")

    # Should see error message
    error_message = page.locator(".alert-warning, .alert-error")
    await expect(error_message).to_be_visible()


async def test_debug_endpoints(page: Page):
    """Test debug endpoints when in debug mode."""
    # Test routes endpoint
    response = await page.goto(f"{HOST}/debug/routes")
    if response and response.ok:
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower()

    # Test config endpoint
    response = await page.goto(f"{HOST}/debug/config")
    if response and response.ok:
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower()
