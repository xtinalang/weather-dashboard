from playwright.sync_api import expect


def test_weather_page_display(page, base_url):
    # Navigate to the weather page using coordinates (e.g., London's coordinates)
    page.goto(f"{base_url}/weather/51.5074/-0.1278")

    # Check that the weather display section is visible
    expect(page.locator(".weather-display")).to_be_visible()

    # Check the location name in the heading
    expect(page.locator("h2")).to_contain_text("Weather for London")

    # Check the region and country
    expect(page.locator('p:has-text("London")')).to_be_visible()

    # Check the last updated timestamp
    expect(page.locator('p:has-text("Last updated:")')).to_be_visible()

    # Check the weather icon (if present)
    expect(page.locator(".weather-icon img")).to_be_visible()

    # Check the condition and temperature
    expect(page.locator(".condition")).to_be_visible()
    expect(page.locator(".temperature")).to_be_visible()

    # Check the "feels like" temperature
    expect(page.locator('div:has-text("Feels like:")')).to_be_visible()

    # Check the weather details (humidity, wind, pressure, precipitation)
    expect(page.locator(".weather-details")).to_be_visible()
    expect(page.locator('p:has-text("Humidity:")')).to_be_visible()
    expect(page.locator('p:has-text("Wind:")')).to_be_visible()
    expect(page.locator('p:has-text("Pressure:")')).to_be_visible()
    expect(page.locator('p:has-text("Precipitation:")')).to_be_visible()

    # Check the navigation links
    expect(page.locator('a:has-text("Back to Home")')).to_be_visible()
    expect(page.locator('a:has-text("View Forecast")')).to_be_visible()
    expect(page.locator('a:has-text("Switch to °C")')).to_be_visible()

    # Optionally, check the favorites button if it exists
    if page.locator('button:has-text("Add to Favorites")').is_visible():
        expect(page.locator('button:has-text("Add to Favorites")')).to_be_visible()


def test_weather_page_invalid_location(page, base_url):
    page.goto(base_url)
    page.fill('input[name="location"]', "InvalidCity123")
    page.click('button:has-text("Get Weather")')
    expect(page.locator(".flash-message")).to_contain_text("Could not find location")
