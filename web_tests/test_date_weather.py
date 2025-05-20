from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()


def test_date_weather_form_loads(page: Page):
    """Test that the date weather form loads correctly"""
    page.goto("http://localhost:5001/date-weather")

    # Check if the form elements are present
    expect(page.locator("h1")).to_contain_text("Check Weather for a Specific Date")
    expect(page.locator("input[type='date']")).to_be_visible()
    expect(page.locator("input[placeholder='Enter city name']")).to_be_visible()
    expect(page.locator("select")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_date_weather_submission(page: Page):
    """Test submitting the date weather form"""
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
    """Test form validation"""
    page.goto("http://localhost:5001/date-weather")

    # Try to submit without filling required fields
    page.click("button[type='submit']")

    # Check for validation messages
    expect(page.locator("input[type='date']")).to_have_attribute("required")
    expect(page.locator("input[placeholder='Enter city name']")).to_have_attribute(
        "required"
    )
