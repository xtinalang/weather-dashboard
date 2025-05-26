import pytest
from playwright.sync_api import sync_playwright

# Test configuration constants
HOST: str = "http://localhost:5001"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()
