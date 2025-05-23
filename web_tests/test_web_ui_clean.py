import pytest
from playwright.sync_api import Page, expect

HOST: str = "http://localhost:5001"


@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()


def test_homepage_loads(page: Page):
    """Test that the homepage loads correctly"""
    page.goto(f"{HOST}/")

    # Check if the main elements are present
    expect(page.locator("h1")).to_contain_text("Weather Dashboard")
    expect(page.locator("form").first).to_be_visible()


def test_form_count_correct(page: Page):
    """Test that all expected forms are present"""
    page.goto(f"{HOST}/")

    # There should be 7 forms total
    forms = page.locator("form")
    expect(forms).to_have_count(7)


def test_essential_form_elements(page: Page):
    """Test that essential form elements are present"""
    page.goto(f"{HOST}/")

    # Test search form
    search_form = page.locator("form[action='/search']")
    expect(search_form).to_be_visible()

    # Test forecast form
    forecast_form = page.locator("form[action='/forecast']").first
    expect(forecast_form).to_be_visible()

    # Test natural language form
    nl_form = page.locator("form[action='/nl-date-weather']")
    expect(nl_form).to_be_visible()


def test_quick_access_cities(page: Page):
    """Test that quick access city forms are present"""
    page.goto(f"{HOST}/")

    # Based on test output, there are 4 city forms (London, New York, Tokyo, Sydney)
    city_forms = page.locator("form[action='/forecast'][method='post']")
    expect(city_forms).to_have_count(4)


def test_navigation_present(page: Page):
    """Test navigation elements are present"""
    page.goto(f"{HOST}/")

    # Check for navigation
    expect(page.locator("nav, .navbar")).to_be_visible()
    expect(page.locator("a:has-text('Weather Dashboard')")).to_be_visible()


def test_form_inputs_visible(page: Page):
    """Test that key form inputs are visible"""
    page.goto(f"{HOST}/")

    # Check for unit selection
    expect(page.locator("select[name='unit']")).to_be_visible()

    # Check for forecast days selection
    expect(page.locator("select[name='forecast_days']")).to_be_visible()

    # Check for natural language input
    expect(page.locator("input[name='query']")).to_be_visible()


def test_csrf_tokens_present(page: Page):
    """Test that CSRF tokens are present in forms"""
    page.goto(f"{HOST}/")

    # Check for CSRF token in forms
    csrf_inputs = page.locator("input[name='csrf_token']")
    assert csrf_inputs.count() > 0, "Should have CSRF tokens in forms"


def test_invalid_coordinates_redirect(page: Page):
    """Test how the app handles invalid coordinates"""
    page.goto(f"{HOST}/weather/999/999")

    # Should redirect to home page
    expect(page).to_have_url(f"{HOST}/")


def test_css_loaded(page: Page):
    """Test that CSS is properly linked"""
    page.goto(f"{HOST}/")

    # Check if CSS is linked
    css_links = page.locator("link[rel='stylesheet']")
    expect(css_links.count()).to_be_greater_than(0)


def test_page_structure_intact(page: Page):
    """Test that basic page structure is intact"""
    page.goto(f"{HOST}/")

    # Should have doctype html
    page_content = page.content()
    assert "<!DOCTYPE html>" in page_content

    # Should have proper head section
    expect(page.locator("head")).to_be_visible()
    expect(page.locator("title")).to_be_visible()

    # Should have body
    expect(page.locator("body")).to_be_visible()


def test_form_actions_correct(page: Page):
    """Test that forms have correct action URLs"""
    page.goto(f"{HOST}/")

    # Natural language form
    nl_form = page.locator("form[action='/nl-date-weather']")
    expect(nl_form).to_be_visible()

    # Search form
    search_form = page.locator("form[action='/search']")
    expect(search_form).to_be_visible()

    # Forecast forms
    forecast_forms = page.locator("form[action='/forecast']")
    expect(forecast_forms.count()).to_be_greater_than(0)
