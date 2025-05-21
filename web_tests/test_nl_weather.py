# Prep for future features
from playwright.sync_api import expect


def test_nl_weather_query(page, base_url):
    """Test natural language weather query functionality"""
    # Navigate to the home page
    page.goto(base_url)

    # Fill in the natural language query
    page.fill('input[name="query"]', "What's the weather in London on Monday?")

    # Submit the form
    page.click('button:has-text("Search")')

    # Wait for the results page to load
    page.wait_for_selector(".weather-display")

    # Verify the location is displayed
    expect(page.locator("h2")).to_contain_text("Forecast for London")

    # Verify weather data is displayed
    expect(page.locator(".temperature")).to_be_visible()
    expect(page.locator(".condition")).to_be_visible()

    # Verify weather details are displayed
    expect(page.locator(".weather-details")).to_be_visible()


def test_nl_weather_invalid_location(page, base_url):
    """Test natural language weather query with invalid location"""
    # Navigate to the home page
    page.goto(base_url)

    # Fill in the natural language query with invalid location
    page.fill('input[name="query"]', "What's the weather in InvalidCity123 on Monday?")

    # Submit the form
    page.click('button:has-text("Search")')

    # Wait for flash message
    page.wait_for_selector(".flash-message")

    # Verify error message is displayed
    expect(page.locator(".flash-message")).to_contain_text("Could not find location")


def test_nl_weather_missing_location(page, base_url):
    """Test natural language weather query without location"""
    # Navigate to the home page
    page.goto(base_url)

    # Fill in the natural language query without location
    page.fill('input[name="query"]', "What's the weather on Monday?")

    # Submit the form
    page.click('button:has-text("Search")')

    # Wait for flash message
    page.wait_for_selector(".flash-message")

    # Verify error message is displayed
    expect(page.locator(".flash-message")).to_contain_text(
        "Could not find a location in your query"
    )


def test_weather_results_display(page, base_url):
    # Go to homepage and submit a valid location
    page.goto(base_url)
    page.fill('input[name="location"]', "London")
    page.click('input[type="submit"][value="Get Weather"]')

    # Wait for the weather display section to appear
    expect(page.locator(".weather-display")).to_be_visible()

    # Check for location name in the heading
    expect(page.locator("h2")).to_contain_text("London")

    # Check for temperature and condition
    expect(page.locator(".temperature")).to_be_visible()
    expect(page.locator(".condition")).to_be_visible()

    # Optionally, check for forecast days and unit
    expect(page.locator(".forecast-days")).to_be_visible()
    expect(page.locator(".unit")).to_be_visible()


def test_weather_page_direct(page, base_url):
    page.goto(f"{base_url}/weather/London")
    expect(page.locator(".weather-display")).to_be_visible()
    # ... other checks as above


def test_weather_page_invalid_location(page, base_url):
    page.goto(base_url)
    page.fill('input[name="location"]', "InvalidCity123")
    page.click('input[type="submit"][value="Get Weather"]')
    expect(page.locator(".flash-message")).to_contain_text("Could not find location")
