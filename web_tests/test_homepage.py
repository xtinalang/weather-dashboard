import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()


def test_homepage_title(page: Page):
    page.goto("http://localhost:5001")
    expect(page).to_have_title("Weather Dashboard")


def test_homepage_heading(page: Page):
    page.goto("http://localhost:5001")
    heading = page.locator("h1")
    expect(heading).to_contain_text("Weather Dashboard")
