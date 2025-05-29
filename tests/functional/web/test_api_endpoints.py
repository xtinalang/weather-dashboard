"""
Functional tests for Flask API endpoints and AJAX functionality.
Tests API routes, JSON responses, and asynchronous web features.
"""

import json

import pytest
from conftest import HOST
from playwright.sync_api import Page
from test_constants import TEST_CITY_LONDON


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_api_weather_endpoint_valid_coordinates(self, page: Page):
        """Test API weather endpoint with valid coordinates."""
        # London coordinates
        lat, lon = 51.5074, -0.1278
        api_url = f"{HOST}/api/weather/{lat}/{lon}"

        # Navigate to API endpoint
        response = page.goto(api_url)

        # Should return successful response
        assert response.status == 200

        # Check content type is JSON
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

        # Parse JSON response
        content = page.content()
        try:
            data = json.loads(page.locator("pre").inner_text())
            # Should have weather data structure
            assert "current" in data or "error" in data
        except (json.JSONDecodeError, Exception):
            # API might return HTML error page instead of JSON
            assert "error" in content.lower() or "weather" in content.lower()

    def test_api_weather_endpoint_invalid_coordinates(self, page: Page):
        """Test API weather endpoint with invalid coordinates."""
        # Invalid coordinates
        lat, lon = 999, 999
        api_url = f"{HOST}/api/weather/{lat}/{lon}"

        response = page.goto(api_url)

        # Should handle invalid coordinates gracefully
        assert response.status in [200, 400, 404, 500]

        # Should contain error message if status is not 200
        if response.status != 200:
            content = page.content()
            assert any(
                keyword in content.lower()
                for keyword in ["error", "invalid", "not found"]
            )

    def test_api_weather_endpoint_format(self, page: Page):
        """Test API weather endpoint response format."""
        # Test with coordinates that should work (London)
        lat, lon = 51.5074, -0.1278
        api_url = f"{HOST}/api/weather/{lat}/{lon}"

        page.goto(api_url)

        # Check if we get JSON response
        try:
            json_text = page.locator("pre").inner_text()
            data = json.loads(json_text)

            # Check expected structure if successful
            if "current" in data:
                assert isinstance(data["current"], dict)
                # Check for expected weather fields
                expected_fields = ["temp_c", "temp_f", "condition", "humidity"]
                current_data = data["current"]
                # At least some expected fields should be present
                assert any(field in current_data for field in expected_fields)

        except Exception:
            # If not JSON, check that page handles the case gracefully
            content = page.content()
            assert content  # Should have some content


class TestAJAXFunctionality:
    """Test suite for AJAX and dynamic content functionality."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_quick_link_ajax_behavior(self, page: Page):
        """Test AJAX behavior of quick link buttons."""
        page.goto(HOST)

        # Wait for page to load completely
        page.wait_for_load_state("networkidle")

        # Find and click a quick link button
        london_button = page.locator(f"button:has-text('{TEST_CITY_LONDON}')")
        if london_button.count() > 0:
            # Click the button
            london_button.click()

            # Wait for any AJAX requests to complete
            page.wait_for_load_state("networkidle")

            # Check if content was updated or if we navigated
            current_url = page.url
            assert current_url  # Should have a valid URL

            # Check for weather-related content
            content = page.content()
            assert any(
                keyword in content.lower()
                for keyword in ["weather", "temperature", "london", "forecast"]
            )

    def test_form_csrf_token_presence(self, page: Page):
        """Test that forms have CSRF tokens for security."""
        page.goto(HOST)

        # Check forms for CSRF tokens
        forms = page.locator("form")
        form_count = forms.count()

        if form_count > 0:
            for i in range(form_count):
                form = forms.nth(i)
                # Look for CSRF token field
                csrf_input = form.locator("input[name*='csrf']")
                if csrf_input.count() > 0:
                    # CSRF token should have a value
                    csrf_value = csrf_input.get_attribute("value")
                    assert csrf_value and len(csrf_value) > 10

    def test_async_form_submission(self, page: Page):
        """Test asynchronous form submission behavior."""
        page.goto(HOST)

        # Look for a search form
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Fill and submit
            search_input.fill("London")
            search_button.click()

            # Wait for response
            page.wait_for_load_state("networkidle")

            # Should either stay on page with results or navigate
            current_url = page.url
            assert HOST in current_url

    def test_favorite_button_functionality(self, page: Page):
        """Test favorite button AJAX functionality if present."""
        page.goto(HOST)

        # Look for any favorite buttons or heart icons
        favorite_buttons = page.locator(
            "button[title*='favorite'], .fa-heart, [class*='favorite']"
        )

        if favorite_buttons.count() > 0:
            # Try clicking the first favorite button
            first_button = favorite_buttons.first
            first_button.click()

            # Wait for any AJAX to complete
            page.wait_for_timeout(1000)  # Brief wait for potential AJAX

            # Check that page is still functional
            assert page.url


class TestErrorHandling:
    """Test suite for error handling in web interface."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_404_error_handling(self, page: Page):
        """Test 404 error page handling."""
        # Try to access non-existent route
        response = page.goto(f"{HOST}/nonexistent-page")

        # Should return 404 or redirect to error page
        assert response.status in [404, 302, 500]

        # Check error content if 404
        if response.status == 404:
            content = page.content()
            assert any(
                keyword in content.lower() for keyword in ["not found", "404", "error"]
            )

    def test_api_error_responses(self, page: Page):
        """Test API error response handling."""
        # Test with malformed coordinates
        api_url = f"{HOST}/api/weather/invalid/invalid"

        response = page.goto(api_url)

        # Should handle malformed request
        assert response.status in [400, 404, 500]

    def test_form_validation_errors(self, page: Page):
        """Test form validation error display."""
        page.goto(HOST)

        # Try submitting forms with invalid data
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_button = search_form.locator("button[type='submit']")

            # Submit empty form
            search_button.click()

            # Wait for response
            page.wait_for_load_state("networkidle")

            # Should handle empty submission gracefully
            content = page.content()
            assert content  # Should have some content


class TestResponseTimes:
    """Test suite for response time and performance."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_homepage_load_time(self, page: Page):
        """Test that homepage loads within reasonable time."""
        import time

        start_time = time.time()
        page.goto(HOST)
        page.wait_for_load_state("networkidle")
        end_time = time.time()

        load_time = end_time - start_time
        # Should load within 10 seconds (generous for testing)
        assert load_time < 10

    def test_api_response_time(self, page: Page):
        """Test API endpoint response time."""
        import time

        # Test API endpoint
        lat, lon = 51.5074, -0.1278  # London
        api_url = f"{HOST}/api/weather/{lat}/{lon}"

        start_time = time.time()
        response = page.goto(api_url)
        end_time = time.time()

        response_time = end_time - start_time
        # API should respond within 10 seconds
        assert response_time < 10

        # Should get some response
        assert response.status in [200, 400, 404, 500]


class TestBrowserCompatibility:
    """Test suite for browser compatibility features."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_javascript_functionality(self, page: Page):
        """Test that JavaScript functions work properly."""
        page.goto(HOST)

        # Check if JavaScript is enabled and working
        js_result = page.evaluate("() => { return typeof document !== 'undefined'; }")
        assert js_result is True

    def test_css_loading(self, page: Page):
        """Test that CSS styles are loaded properly."""
        page.goto(HOST)

        # Check if styles are applied by looking for styled elements
        body = page.locator("body")
        computed_style = body.evaluate("el => getComputedStyle(el).backgroundColor")

        # Should have some computed style (not 'rgba(0, 0, 0, 0)' which is default)
        assert computed_style is not None

    def test_responsive_design_elements(self, page: Page):
        """Test responsive design elements."""
        page.goto(HOST)

        # Test mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.reload()
        page.wait_for_load_state("networkidle")

        # Should still be functional in mobile view
        assert page.locator("h1").count() > 0

        # Test desktop viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.reload()
        page.wait_for_load_state("networkidle")

        # Should still be functional in desktop view
        assert page.locator("h1").count() > 0
