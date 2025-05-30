"""
Health check and core functionality tests for the Weather Dashboard.
"""

from playwright.sync_api import Page, expect

# Update this to match your application's host and port
HOST = "http://localhost:5001"


def test_homepage_loads(page: Page):
    """Test that the homepage loads and contains essential elements."""
    response = page.goto(HOST)
    assert response and response.ok, "Homepage failed to load"

    # Check main components
    expect(page).to_have_title("Weather Dashboard")
    expect(page.locator("form[action*='search']")).to_be_visible()
    expect(page.locator("input[name='query']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_search_functionality(page: Page):
    """Test the search functionality with a known city."""
    page.goto(HOST)

    # Fill and submit the search form
    search_input = page.locator("input[name='query']")
    search_button = page.locator("form[action*='search'] button[type='submit']")

    search_input.fill("London")
    search_button.click()

    # Wait for navigation and check results
    page.wait_for_load_state("networkidle")

    # We should either see weather results or location selection
    success = (
        page.locator(".weather-data").is_visible()
        or page.locator(".location-selection").is_visible()
    )
    assert success, "Search results not displayed"


def test_natural_language_query(page: Page):
    """Test the natural language weather query functionality."""
    page.goto(HOST)

    # Find and fill the NL query form
    nl_input = page.locator("input[name='query']").nth(1)  # Second query input on page
    nl_button = page.locator("form[action*='nl-date-weather'] button[type='submit']")

    nl_input.fill("What's the weather like in London tomorrow?")
    nl_button.click()

    # Wait for navigation and check results
    page.wait_for_load_state("networkidle")

    # Should see either weather results or location selection
    success = (
        page.locator(".weather-data").is_visible()
        or page.locator(".location-selection").is_visible()
    )
    assert success, "Natural language query results not displayed"


def test_unit_toggle(page: Page):
    """Test temperature unit toggle functionality."""
    page.goto(HOST)

    # Find and click unit toggle
    unit_form = page.locator("form[action*='unit']")
    unit_options = unit_form.locator("input[name='unit']")

    # Try to change unit
    if unit_options.nth(1).is_visible():
        unit_options.nth(1).click()
        unit_form.locator("button[type='submit']").click()

        # Wait for reload
        page.wait_for_load_state("networkidle")

        # Verify the change was saved
        assert page.url == HOST, "Unit change should redirect to homepage"


def test_forecast_days(page: Page):
    """Test forecast days selection functionality."""
    page.goto(HOST)

    # Find and change forecast days
    forecast_form = page.locator("form[action*='forecast']")
    forecast_select = forecast_form.locator("select[name='forecast_days']")

    if forecast_select.is_visible():
        # Select a different value
        forecast_select.select_option("5")
        forecast_form.locator("button[type='submit']").click()

        # Wait for reload
        page.wait_for_load_state("networkidle")

        # Verify we're back on homepage
        assert page.url == HOST, "Forecast days change should redirect to homepage"


def test_error_handling(page: Page):
    """Test error handling with invalid input."""
    page.goto(HOST)

    # Try invalid search
    search_input = page.locator("input[name='query']")
    search_button = page.locator("form[action*='search'] button[type='submit']")

    search_input.fill("!@#$%")
    search_button.click()

    # Wait for navigation
    page.wait_for_load_state("networkidle")

    # Should see error message
    error_message = page.locator(".alert-warning, .alert-error")
    expect(error_message).to_be_visible()


def test_debug_endpoints(page: Page):
    """Test debug endpoints when in debug mode."""
    # Test routes endpoint
    response = page.goto(f"{HOST}/debug/routes")
    if response and response.ok:
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower()

    # Test config endpoint
    response = page.goto(f"{HOST}/debug/config")
    if response and response.ok:
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower()
