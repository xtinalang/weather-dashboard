"""Integration tests for date weather functionality."""

from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test."""
    page = browser.new_page()
    yield page
    page.close()


def test_homepage_loads(page: Page):
    """Test that the homepage loads correctly."""
    page.goto("http://localhost:5001/")

    # Check if the main elements are present
    expect(page.locator("h1")).to_contain_text("Weather Dashboard")
    expect(page.locator("form")).to_be_visible()
    expect(page.locator("input[name='query']")).to_be_visible()
    expect(page.locator("select[name='unit']")).to_be_visible()


def test_search_form_visible(page: Page):
    """Test that search forms are visible on homepage."""
    page.goto("http://localhost:5001/")

    # Check for location search form
    expect(page.locator("input[placeholder*='city']")).to_be_visible()

    # Check for unit selection
    expect(page.locator("select[name='unit']")).to_be_visible()

    # Check for forecast days selection
    expect(page.locator("select[name='forecast_days']")).to_be_visible()


def test_natural_language_form_visible(page: Page):
    """Test that natural language weather form is visible."""
    page.goto("http://localhost:5001/")

    # Check for natural language form elements
    expect(page.locator("textarea[name='query']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_location_search_form_validation(page: Page):
    """Test location search form validation."""
    page.goto("http://localhost:5001/")

    # Find the location search form specifically
    search_form = page.locator("form").filter(has=page.locator("input[name='query']"))

    # Try to submit without entering a location
    search_button = search_form.locator("button[type='submit']")
    search_button.click()

    # Should stay on the same page or show validation
    expect(page).to_have_url("http://localhost:5001/")


def test_popular_cities_links(page: Page):
    """Test that popular cities quick links are present."""
    page.goto("http://localhost:5001/")

    # Check for popular cities section
    expect(page.locator("h3:has-text('Popular Cities')")).to_be_visible()

    # The page should have some city links
    expect(page.locator("a[href*='forecast']")).to_have_count(
        5
    )  # Based on the 5 popular cities


def test_api_endpoint_weather(page: Page):
    """Test the API endpoint returns JSON."""
    response = page.request.get(
        "http://localhost:5001/api/weather/51.5074/-0.1278"
    )  # London coordinates

    # Should return JSON
    expect(response).to_be_ok()

    json_data = response.json()
    assert "current" in json_data
    assert "temp_c" in json_data["current"]


def test_invalid_coordinates_handling(page: Page):
    """Test how the app handles invalid coordinates."""
    page.goto("http://localhost:5001/weather/invalid/coordinates")

    # Should redirect to home page with error message
    expect(page).to_have_url("http://localhost:5001/")

    # Check for flash message (if visible)
    flash_message = page.locator(".flash-message, .alert")
    if flash_message.count() > 0:
        expect(flash_message).to_be_visible()


def test_navigation_elements(page: Page):
    """Test navigation elements are present."""
    page.goto("http://localhost:5001/")

    # Check for navigation
    expect(page.locator("nav, .navbar")).to_be_visible()
    expect(page.locator("a:has-text('Weather Dashboard')")).to_be_visible()


def test_csrf_protection(page: Page):
    """Test that CSRF tokens are present in forms."""
    page.goto("http://localhost:5001/")

    # Check for CSRF token in forms
    csrf_input = page.locator("input[name='csrf_token']")
    expect(csrf_input).to_have_count(3)  # Should have CSRF tokens in forms


def test_date_weather_form_loads(page: Page):
    """Test that the date weather form loads correctly."""
    page.goto("http://localhost:5001/date-weather")

    # Check if the form elements are present
    expect(page.locator("h1")).to_contain_text("Check Weather for a Specific Date")
    expect(page.locator("input[type='date']")).to_be_visible()
    expect(page.locator("input[placeholder='Enter city name']")).to_be_visible()
    expect(page.locator("select")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_date_weather_submission(page: Page):
    """Test submitting the date weather form."""
    page.goto("http://localhost:5001/date-weather")

    # Fill in the form
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    page.fill("input[type='date']", tomorrow)
    page.fill("input[placeholder='Enter city name']", "London")
    page.select_option("select", "C")

    # Submit the form
    page.click("button[type='submit']")

    # Check if we get redirected to the results page
    expect(page).to_have_url("http://localhost:5001/date-weather")
    expect(page.locator("h1")).to_contain_text("Weather for London")

    # Check if weather data is displayed
    expect(page.locator("strong:has-text('Temperature')")).to_be_visible()
    expect(page.locator("strong:has-text('Conditions')")).to_be_visible()
    expect(page.locator("strong:has-text('Humidity')")).to_be_visible()


def test_date_weather_validation(page: Page):
    """Test form validation."""
    page.goto("http://localhost:5001/date-weather")

    # Try to submit without filling required fields
    page.click("button[type='submit']")

    # Check for validation messages
    expect(page.locator("input[type='date']")).to_have_attribute("required")
    expect(page.locator("input[placeholder='Enter city name']")).to_have_attribute(
        "required"
    )
