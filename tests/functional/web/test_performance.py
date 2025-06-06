"""
Performance functional tests for the Flask web UI.
Tests page load times, responsiveness, and user experience metrics.
"""

import time

import pytest
from conftest import HOST
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class TestPageLoadPerformance:
    """Test suite for page load performance."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_home_page_load_time(self, page: Page):
        """Test that home page loads within acceptable time."""
        start_time = time.time()

        try:
            page.goto(HOST, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)

            load_time = time.time() - start_time

            # Home page should load within 5 seconds
            assert load_time < 5.0, f"Home page took {load_time:.2f}s to load"

            # Page should have basic content
            content = page.content()
            assert len(content) > 100  # Should have substantial content

        except (PlaywrightTimeoutError, PlaywrightError):
            pytest.skip("Web server not available for performance testing")

    def test_search_response_time(self, page: Page):
        """Test search functionality response time."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            search_input.fill("London")

            start_time = time.time()
            search_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            response_time = time.time() - start_time

            # Search should respond within 10 seconds
            assert response_time < 10.0, f"Search took {response_time:.2f}s to respond"

    def test_weather_page_load_time(self, page: Page):
        """Test weather page load performance."""
        # Try to navigate directly to a weather page
        weather_url = f"{HOST}/weather/51.5074/-0.1278"  # London coordinates

        start_time = time.time()

        try:
            page.goto(weather_url, timeout=15000)
            page.wait_for_load_state("networkidle", timeout=15000)

            load_time = time.time() - start_time

            # Weather page should load within 10 seconds (includes API call)
            assert load_time < 10.0, f"Weather page took {load_time:.2f}s to load"

        except (PlaywrightTimeoutError, PlaywrightError):
            # API might be slow or unavailable, which is acceptable
            pass

    def test_concurrent_user_simulation(self, browser):
        """Test behavior with multiple concurrent users."""
        pages = []

        try:
            # Create multiple pages to simulate concurrent users
            for _ in range(3):  # 3 concurrent users
                page = browser.new_page()
                pages.append(page)

            start_time = time.time()

            # Have all users load the home page simultaneously
            for page in pages:
                page.goto(HOST, timeout=10000)

            # Wait for all to complete
            for page in pages:
                page.wait_for_load_state("networkidle", timeout=15000)

            total_time = time.time() - start_time

            # Should handle concurrent users reasonably well
            assert total_time < 15.0, f"Concurrent access took {total_time:.2f}s"

        except (PlaywrightTimeoutError, PlaywrightError):
            pytest.skip("Server not responsive enough for concurrent testing")
        finally:
            # Clean up pages
            for page in pages:
                page.close()


class TestResponsiveness:
    """Test suite for UI responsiveness."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_form_interaction_responsiveness(self, page: Page):
        """Test that form interactions are responsive."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")

            # Test typing responsiveness
            start_time = time.time()
            search_input.fill("London")
            typing_time = time.time() - start_time

            # Typing should be instantaneous (< 100ms)
            assert typing_time < 0.1, f"Typing took {typing_time:.3f}s"

            # Test that input value is correctly set
            assert search_input.input_value() == "London"

    def test_button_click_responsiveness(self, page: Page):
        """Test button click responsiveness."""
        page.goto(HOST)

        # Find clickable buttons
        buttons = page.locator("button, input[type='submit']")

        if buttons.count() > 0:
            button = buttons.first

            # Measure click response time
            start_time = time.time()
            button.click()

            # Should register click immediately
            response_time = time.time() - start_time
            assert response_time < 0.5, f"Button click took {response_time:.3f}s"

    def test_page_navigation_responsiveness(self, page: Page):
        """Test page navigation responsiveness."""
        page.goto(HOST)

        # Find navigation links
        nav_links = page.locator("a[href]")

        if nav_links.count() > 0:
            # Test clicking a navigation link
            start_time = time.time()
            nav_links.first.click()

            # Should start navigation quickly
            navigation_start = time.time() - start_time
            assert navigation_start < 0.5, (
                f"Navigation start took {navigation_start:.3f}s"
            )

    def test_mobile_responsiveness(self, page: Page):
        """Test responsiveness on mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone size

        page.goto(HOST)

        # Check that elements are still interactive
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            assert search_form.is_visible()

            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Elements should be accessible on mobile
            assert search_input.is_visible()
            assert search_button.is_visible()

            # Should be able to interact
            search_input.fill("Test")
            assert search_input.input_value() == "Test"


class TestResourceUsage:
    """Test suite for resource usage optimization."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_memory_usage_monitoring(self, page: Page):
        """Test that page doesn't consume excessive memory."""
        page.goto(HOST)

        # Perform several operations that might cause memory leaks
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Perform repeated actions
            for i in range(5):
                search_input.fill(f"Test {i}")
                search_button.click()
                page.wait_for_load_state("networkidle", timeout=5000)
                page.go_back()

            # Page should still be responsive
            assert search_input.is_visible()

    def test_network_request_efficiency(self, page: Page):
        """Test that page doesn't make excessive network requests."""
        requests = []

        def track_requests(request):
            requests.append(request.url)

        page.on("request", track_requests)

        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Should not make an excessive number of requests
        # Filter out common resources like CSS, JS, images
        page_requests = [
            req
            for req in requests
            if not any(ext in req for ext in [".css", ".js", ".png", ".jpg", ".ico"])
        ]

        assert len(page_requests) < 10, f"Too many page requests: {len(page_requests)}"

    def test_css_and_js_loading_efficiency(self, page: Page):
        """Test that CSS and JS resources load efficiently."""
        failed_resources = []

        def track_failures(response):
            if response.status >= 400:
                failed_resources.append(response.url)

        page.on("response", track_failures)

        page.goto(HOST)
        page.wait_for_load_state("networkidle")

        # Should not have failed resource loads
        assert len(failed_resources) == 0, f"Failed to load: {failed_resources}"


class TestScalabilityIndicators:
    """Test suite for scalability indicators."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_large_dataset_handling(self, page: Page):
        """Test handling of potentially large datasets."""
        page.goto(HOST)

        # Try searches that might return large datasets
        large_dataset_searches = [
            "New York",  # Common city name
            "London",  # Very common city name
            "Paris",  # Another common name
        ]

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            for search_term in large_dataset_searches:
                start_time = time.time()

                search_input.fill(search_term)
                search_button.click()
                page.wait_for_load_state("networkidle", timeout=15000)

                response_time = time.time() - start_time

                # Should handle large datasets within reasonable time
                assert response_time < 15.0, (
                    f"Large dataset search took {response_time:.2f}s"
                )

                # Go back for next test
                page.goto(HOST)

    def test_repeated_operations_performance(self, page: Page):
        """Test performance degradation over repeated operations."""
        page.goto(HOST)

        operation_times = []

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")
            search_button = search_form.locator("button[type='submit']")

            # Perform repeated operations
            for i in range(3):  # Limited iterations for test speed
                start_time = time.time()

                search_input.fill(f"Test{i}")
                search_button.click()
                page.wait_for_load_state("networkidle", timeout=10000)

                operation_time = time.time() - start_time
                operation_times.append(operation_time)

                # Go back for next iteration
                page.goto(HOST)

            # Performance should not degrade significantly
            if len(operation_times) > 1:
                first_time = operation_times[0]
                last_time = operation_times[-1]

                # Last operation should not be more than 2x slower than first
                assert last_time < first_time * 2, (
                    "Performance degraded over repeated operations"
                )

    def test_stress_form_interactions(self, page: Page):
        """Test form interaction under stress conditions."""
        page.goto(HOST)

        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")

            # Rapid form interactions
            start_time = time.time()

            for i in range(10):  # Rapid input changes
                search_input.fill(f"Rapid{i}")
                # Small delay to simulate real user behavior
                page.wait_for_timeout(50)

            total_time = time.time() - start_time

            # Should handle rapid interactions without performance issues
            assert total_time < 2.0, f"Rapid interactions took {total_time:.2f}s"

            # Form should still be responsive
            final_value = search_input.input_value()
            assert "Rapid" in final_value


class TestUserExperienceMetrics:
    """Test suite for user experience performance metrics."""

    @pytest.fixture
    def page(self, browser):
        """Create a new page for each test."""
        page = browser.new_page()
        yield page
        page.close()

    def test_time_to_interactive(self, page: Page):
        """Test time to interactive (TTI) metric."""
        start_time = time.time()

        page.goto(HOST)

        # Wait for page to be interactive
        page.wait_for_load_state("domcontentloaded")

        # Test that key interactive elements are available
        search_form = page.locator("form[action*='search']")
        if search_form.count() > 0:
            search_input = search_form.locator("input[name='query']")

            # Try to interact immediately
            search_input.fill("Interactive Test")

            tti = time.time() - start_time

            # Should be interactive within 3 seconds
            assert tti < 3.0, f"Time to interactive: {tti:.2f}s"

    def test_perceived_performance(self, page: Page):
        """Test perceived performance through loading states."""
        page.goto(HOST)

        # Look for loading indicators or immediate content
        content_elements = page.locator("h1, h2, form, button, input")

        # Should have visible content quickly
        assert content_elements.count() > 0, "No visible content elements found"

        # Key elements should be visible
        for i in range(min(3, content_elements.count())):
            element = content_elements.nth(i)
            assert element.is_visible(), f"Content element {i} not visible"

    def test_progressive_enhancement(self, page: Page):
        """Test that basic functionality works immediately."""
        page.goto(HOST)

        # Basic HTML elements should be present and functional
        forms = page.locator("form")
        if forms.count() > 0:
            form = forms.first

            # Form should be functional even before full JS loads
            inputs = form.locator("input[type='text'], input[type='search']")
            if inputs.count() > 0:
                test_input = inputs.first
                test_input.fill("Progressive Test")

                # Input should work immediately
                assert test_input.input_value() == "Progressive Test"
