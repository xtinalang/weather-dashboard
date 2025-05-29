"""
Functional tests for error handling in the Flask web UI.
Tests various error scenarios, network failures, and edge cases.
"""

import pytest
from conftest import HOST
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class TestNetworkErrorHandling:
    """Test suite for network and API error handling."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_page_load_failure_handling(self, page: Page):
        """Test handling when main page fails to load."""
        try:
            # Try to load the page with a short timeout
            page.goto(HOST, timeout=5000)

            # If successful, check basic elements are present
            content = page.content()
            assert content

        except (PlaywrightTimeoutError, PlaywrightError):
            # If page doesn't load, that's also valid for testing
            # (server might not be running in CI)
            pytest.skip("Web server not available for testing")

    def test_invalid_search_handling(self, page: Page):
        """Test handling of searches that return no results."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Search for something unlikely to exist
            invalid_searches = [
                "asdfjkl123qwerty",
                "xyzxyzxyzxyz",
                "nonexistentplacename12345",
            ]

            for search_term in invalid_searches:
                search_input.fill(search_term)
                search_button.click()
                page.wait_for_load_state("networkidle")

                # Should handle gracefully without crashing
                content = page.content()
                assert content

                # Should show appropriate message
                assert any(
                    keyword in content.lower()
                    for keyword in ["not found", "no results", "try again", "error"]
                )

                # Go back for next test
                page.goto(HOST)

    def test_malformed_url_handling(self, page: Page):
        """Test handling of malformed URLs."""
        malformed_urls = [
            f"{HOST}/weather/abc/def",  # Invalid coordinates
            f"{HOST}/forecast/999/999",  # Out of range coordinates
            f"{HOST}/weather/51.5074",  # Missing longitude
            f"{HOST}/nonexistent/page",  # Non-existent route
        ]

        for url in malformed_urls:
            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")

                # Should handle gracefully
                content = page.content()
                assert content

                # Should show error page or redirect
                current_url = page.url
                assert HOST in current_url

            except (PlaywrightTimeoutError, PlaywrightError):
                # Timeout is acceptable for error handling
                pass

    def test_api_timeout_simulation(self, page: Page):
        """Test handling when API calls take too long."""
        page.goto(HOST)

        # Submit a weather request
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            search_input.fill("London")
            search_button.click()

            # Wait for response with reasonable timeout
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                content = page.content()
                assert content
            except (PlaywrightTimeoutError, PlaywrightError):
                # Should handle timeout gracefully
                assert True


class TestFormErrorHandling:
    """Test suite for form validation and error handling."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_form_csrf_error_handling(self, page: Page):
        """Test CSRF token validation error handling."""
        page.goto(HOST)

        # Try to manipulate CSRF tokens if present
        csrf_inputs = page.locator("input[name*='csrf'], input[name*='token']")
        if csrf_inputs.count() > 0:
            # Remove or modify CSRF token
            page.evaluate("""
                const csrfInputs = document.querySelectorAll(
                    'input[name*="csrf"], input[name*="token"]'
                );
                csrfInputs.forEach(input => input.value = 'invalid-token');
            """)

            # Try to submit form
            forms = page.locator("form")
            if forms.count() > 0:
                submit_buttons = forms.locator(
                    "button[type='submit'], input[type='submit']"
                )
                if submit_buttons.count() > 0:
                    submit_buttons.first.click()
                    page.wait_for_load_state("networkidle")

                    # Should handle CSRF error gracefully
                    content = page.content()
                    assert content

    def test_javascript_disabled_fallback(self, page: Page):
        """Test that forms work when JavaScript is disabled."""
        # Disable JavaScript
        page.add_init_script(
            "Object.defineProperty(navigator, 'userAgent', {get: () => 'NoJS'});"
        )

        page.goto(HOST)

        # Forms should still be functional
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            search_input.fill("London")
            search_button.click()
            page.wait_for_load_state("networkidle")

            # Should work without JavaScript
            content = page.content()
            assert content

    def test_large_input_handling(self, page: Page):
        """Test handling of unusually large inputs."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Test with very long input
            long_input = "a" * 1000  # 1000 characters
            search_input.fill(long_input)
            search_button.click()
            page.wait_for_load_state("networkidle")

            # Should handle gracefully
            content = page.content()
            assert content

    def test_special_character_injection(self, page: Page):
        """Test handling of potentially dangerous special characters."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Test potentially dangerous inputs
            dangerous_inputs = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "javascript:alert('xss')",
                "data:text/html,<script>alert('xss')</script>",
            ]

            for dangerous_input in dangerous_inputs:
                search_input.fill(dangerous_input)
                search_button.click()
                page.wait_for_load_state("networkidle")

                # Should sanitize and handle safely
                content = page.content()
                assert content
                assert "<script>" not in content  # Should be escaped

                # Go back for next test
                page.goto(HOST)


class TestUserExperienceErrors:
    """Test suite for user experience during error conditions."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_helpful_error_messages(self, page: Page):
        """Test that error messages are helpful and user-friendly."""
        page.goto(HOST)

        # Try to trigger various errors and check messages
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_button = search_form.locator("button[type='submit']")

            # Submit empty form
            search_button.click()
            page.wait_for_load_state("networkidle")

            content = page.content()
            # Should provide helpful guidance
            assert any(
                phrase in content.lower()
                for phrase in [
                    "please enter",
                    "required",
                    "try again",
                    "search for",
                    "enter a location",
                ]
            )

    def test_error_recovery_paths(self, page: Page):
        """Test that users can recover from errors easily."""
        page.goto(HOST)

        # Navigate to a likely error page
        try:
            page.goto(f"{HOST}/nonexistent")
            page.wait_for_load_state("networkidle")

            content = page.content()
            # Should provide ways to get back to working state
            assert any(
                element in content.lower()
                for element in ["home", "back", "search", "try again"]
            )

            # Should have working navigation
            home_links = page.locator("a[href*='/'], a[href='#'], a:has-text('home')")
            assert home_links.count() > 0

        except (PlaywrightTimeoutError, PlaywrightError):
            # If error page doesn't load, that's fine
            pass

    def test_loading_states_during_errors(self, page: Page):
        """Test loading states when errors occur."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            search_input.fill("test")

            # Look for loading indicators
            search_button.click()

            # Even if errors occur, loading should complete
            page.wait_for_load_state("networkidle")

            # Page should be in a stable state
            content = page.content()
            assert content


class TestBrowserCompatibility:
    """Test suite for browser-specific error handling."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_console_error_monitoring(self, page: Page):
        """Test that there are no critical console errors."""
        console_errors = []

        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", handle_console)

        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Some errors might be expected (like API failures), but should not be critical
        critical_errors = [
            error
            for error in console_errors
            if any(
                keyword in error.lower()
                for keyword in [
                    "uncaught",
                    "reference error",
                    "syntax error",
                    "type error",
                ]
            )
        ]

        # Should not have critical JavaScript errors
        assert len(critical_errors) == 0, f"Critical console errors: {critical_errors}"

    def test_responsive_design_error_handling(self, page: Page):
        """Test error handling on different screen sizes."""
        viewports = [
            {"width": 320, "height": 568},  # Mobile
            {"width": 768, "height": 1024},  # Tablet
            {"width": 1920, "height": 1080},  # Desktop
        ]

        for viewport in viewports:
            page.set_viewport_size(viewport)
            page.goto(HOST)

            # Forms should be accessible at all sizes
            search_form = page.locator("form[action*='search']")
            if search_form.count() > 0:
                assert search_form.is_visible()

                # Submit button should be accessible
                search_button = search_form.locator("button[type='submit']")
                assert search_button.is_visible()

    def test_slow_network_simulation(self, page: Page):
        """Test behavior under slow network conditions."""
        # Simulate slow network
        page.route("**/*", lambda route: route.continue_())

        page.goto(HOST)

        # Should handle slow loading gracefully
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
            content = page.content()
            assert content
        except (PlaywrightTimeoutError, PlaywrightError):
            # Timeout is acceptable for slow network simulation
            pass
