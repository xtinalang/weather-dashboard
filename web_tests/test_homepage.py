import pytest
from playwright.sync_api import expect


@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()


def test_homepage_title(page, base_url):
    """Test homepage title"""
    page.goto(base_url)
    expect(page).to_have_title("Weather Dashboard - Home")


def test_homepage_heading(page, base_url):
    """Test homepage heading"""
    page.goto(base_url)
    expect(page.locator('h1:has-text("Weather Dashboard")')).to_be_visible()


def test_homepage_forms(page, base_url):
    """Test homepage forms and their elements"""
    # Navigate to the home page
    page.goto(base_url)

    # Test search form
    expect(page.locator('input[name="query"]')).to_be_visible()
    expect(page.locator('input[type="submit"][value="Search"]')).to_be_visible()

    # Test location entry form (use the section heading to scope the search)
    location_section = page.locator('h2:has-text("Weather Location Entry")').locator(
        ".."
    )
    expect(location_section.locator('input[name="location"]')).to_be_visible()
    expect(
        location_section.locator('input[type="submit"][value="Get Weather"]')
    ).to_be_visible()


def test_quick_links(page, base_url):
    """Test quick links section"""
    # Navigate to the home page
    page.goto(base_url)

    # Check if quick links section exists
    expect(page.locator('h2:has-text("Popular Cities")')).to_be_visible()
    expect(page.locator(".quick-links")).to_be_visible()

    # Verify quick link buttons
    expect(page.locator('button:has-text("London")')).to_be_visible()
    expect(page.locator('button:has-text("New York")')).to_be_visible()
    expect(page.locator('button:has-text("Tokyo")')).to_be_visible()
    expect(page.locator('button:has-text("Sydney")')).to_be_visible()


def test_favorites_section(page, base_url):
    """Test favorites section if it exists"""
    # Navigate to the home page
    page.goto(base_url)

    # Check if favorites section exists
    favorites_section = page.locator('h2:has-text("Favorite Locations")')
    if favorites_section.is_visible():
        # If favorites exist, verify the structure
        expect(page.locator(".favorites")).to_be_visible()
        # Check first favorite item if it exists
        first_favorite = page.locator(".favorite-item").first
        if first_favorite.is_visible():
            expect(first_favorite).to_be_visible()


def test_navigation_links(page, base_url):
    """Test navigation links and buttons"""
    # Navigate to the home page
    page.goto(base_url)

    # Verify form actions using robust selectors
    search_form = page.locator("form").filter(has_text="Search")
    expect(search_form).to_be_visible()

    location_form = page.locator("form").filter(has_text="Get Weather")
    expect(location_form).to_be_visible()

    # Optionally, you can test form submissions if you want, but this may require more setup
    # search_form.submit()
    # expect(page).to_have_url(f"{base_url}/search")
    # page.goto(base_url)  # Go back to home page
    # location_form.submit()
    # expect(page).to_have_url(f"{base_url}/ui_location")
