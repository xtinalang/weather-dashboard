# Prep for future features
from playwright.sync_api import expect


def test_date_weather_form(page, base_url):
    """Test date weather form functionality"""
    # Navigate to the home page first
    page.goto(base_url)

    # Fill in the form using the UI location form
    page.fill('input[name="location"]', "London")

    # Submit the form
    page.click('button:has-text("Get Weather")')

    # Wait for the results page to load
    page.wait_for_selector(".weather-display")

    # Verify the location is displayed
    expect(page.locator("h2")).to_contain_text("Forecast for London")

    # Verify weather data is displayed
    expect(page.locator(".temperature")).to_be_visible()
    expect(page.locator(".condition")).to_be_visible()

    # Verify weather details are displayed
    expect(page.locator(".weather-details")).to_be_visible()


def test_date_weather_invalid_date(page, base_url):
    """Test date weather form with invalid date"""
    # Navigate to the home page
    page.goto(base_url)

    # Fill in the form with invalid date
    page.fill('input[name="location"]', "London")
    page.fill('input[name="date"]', "invalid-date")

    # Submit the form
    page.click('button[type="submit"]')

    # Verify error message is displayed
    expect(page.locator(".flash-message")).to_contain_text("Invalid date format")


def test_date_weather_invalid_location(page, base_url):
    """Test date weather form with invalid location"""
    # Navigate to the home page
    page.goto(base_url)

    # Fill in the form with invalid location
    page.fill('input[name="location"]', "InvalidCity123")

    # Submit the form
    page.click('button:has-text("Get Weather")')

    # Wait for flash message
    page.wait_for_selector(".flash-message")

    # Verify error message is displayed
    expect(page.locator(".flash-message")).to_contain_text("Could not find location")
