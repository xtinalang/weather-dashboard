import os
import subprocess
import time

import pytest
import requests
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for the web application."""
    return "http://localhost:5001"


@pytest.fixture(scope="session")
def server():
    """Start the Flask server before tests and stop it after."""
    # Start the Flask server
    server_process = subprocess.Popen(
        ["make", "run-flask"],
        env=dict(os.environ, FLASK_ENV="testing", FLASK_DEBUG="0"),
    )

    # Wait for server to be ready
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:5001/")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                raise Exception("Could not connect to Flask server") from None
            time.sleep(1)

    yield server_process

    # Cleanup: stop the server
    server_process.terminate()
    server_process.wait()


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for all tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test."""
    page = browser.new_page()
    yield page
    page.close()
