import pytest_asyncio
from playwright.async_api import async_playwright

# Test configuration constants
HOST: str = "http://localhost:5001"


@pytest_asyncio.fixture(scope="session")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest_asyncio.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    yield page
    await page.close()
