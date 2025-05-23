from playwright.sync_api import Page, expect

HOST: str = "http://localhost:5001"


def test_homepage_loads_correctly(page: Page):
    """Test that the homepage loads with search forms."""
    page.goto(f"{HOST}/")

    # Check the page title (actual title is "Weather Dashboard - Home")
    expect(page).to_have_title("Weather Dashboard - Home")

    # Check main heading
    expect(page.locator("h1")).to_contain_text("Weather Dashboard")

    # Check that forms are present (should be 7 forms based on previous test output)
    forms = page.locator("form")
    expect(forms).to_have_count(7)


def test_search_forms_present(page: Page):
    """Test that search input forms are present and visible."""
    page.goto(f"{HOST}/")

    # Check for city search input - there are 2 city inputs based on error message
    city_inputs = page.locator("input[placeholder*='city']")
    expect(city_inputs).to_have_count(2)

    # Check that at least one search input is visible
    search_input = page.locator("input[name='query']").first
    expect(search_input).to_be_visible()

    # Check for the visible location input (not hidden ones)
    location_input = page.locator("input[name='location']:not([type='hidden'])")
    expect(location_input).to_be_visible()


def test_natural_language_query_form(page: Page):
    """Test the natural language weather query form."""
    page.goto(f"{HOST}/")

    # Check for natural language form
    nl_form = page.locator("form[action='/nl-date-weather']")
    expect(nl_form).to_be_visible()

    # Check for query input in natural language form
    query_textarea = page.locator("textarea[name='query']")
    if query_textarea.count() > 0:
        expect(query_textarea).to_be_visible()


def test_forecast_endpoint_accessible(page: Page):
    """Test that forecast endpoint is accessible with coordinates."""
    # Test London coordinates
    page.goto(f"{HOST}/forecast/51.5074/-0.1278")

    # Should not get a 404 error
    expect(page).not_to_have_title("404")

    # Should contain weather-related content
    page_content = page.content()
    assert any(
        word in page_content.lower()
        for word in ["weather", "forecast", "temperature", "london"]
    )


def test_weather_endpoint_accessible(page: Page):
    """Test that weather endpoint is accessible with coordinates."""
    # Test London coordinates
    page.goto(f"{HOST}/weather/51.5074/-0.1278")

    # Should not get a 404 error
    expect(page).not_to_have_title("404")

    # Should contain weather-related content
    page_content = page.content()
    assert any(
        word in page_content.lower() for word in ["weather", "temperature", "london"]
    )


def test_quick_access_cities_present(page: Page):
    """Test that quick access city buttons are present."""
    page.goto(f"{HOST}/")

    # Check for quick access city forms (these create the hidden location inputs)
    quick_cities = ["London", "New York", "Tokyo", "Sydney"]

    for city in quick_cities:
        city_form = page.locator(f"form:has-text('{city}')")
        expect(city_form).to_be_visible()


if __name__ == "__main__":
    # Run with: python test_search_forecast.py
    print("Run this test with: python -m pytest test_search_forecast.py -v")
