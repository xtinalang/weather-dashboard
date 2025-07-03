#!/usr/bin/env python3
"""
Playwright test script to diagnose location data issues in the Flask web UI.
"""

import asyncio

from playwright.async_api import Page, async_playwright


class WebUITester:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url

    async def test_location_search(self):
        """Test location search functionality"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False
            )  # Set to False to see what happens
            page = await browser.new_page()

            print("🔍 Testing Location Search Functionality")

            try:
                # Navigate to home page
                print(f"📍 Navigating to {self.base_url}")
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                # Take screenshot of initial state
                await page.screenshot(path="screenshots/01_homepage.png")
                print("📸 Screenshot saved: 01_homepage.png")

                # Test 1: Regular Location Search (second form)
                print("\n🔍 Testing regular location search")
                search_form = page.locator('form[action="/search"]')
                search_input = search_form.locator('input[name="query"]')

                if await search_input.count() > 0:
                    print("✅ Regular search form found")
                    await search_input.fill("London")

                    # Find and click search button in this specific form
                    search_button = search_form.locator('button[type="submit"]')
                    await search_button.click()

                    # Wait for response
                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path="screenshots/02_search_results.png")
                    print("📸 Screenshot saved: 02_search_results.png")

                    # Check for errors or results
                    await self.check_for_errors(page, "Regular search")

                    # Check for location selection page
                    location_radios = page.locator(
                        'input[type="radio"][name="selected_location"]'
                    )
                    if await location_radios.count() > 0:
                        print(
                            f"✅ Found {await location_radios.count()} location options"
                        )

                        # Select first location and submit
                        await location_radios.first.check()
                        submit_button = page.locator(
                            'input[type="submit"][value="Get Weather"]'
                        )
                        await submit_button.click()

                        await page.wait_for_load_state("networkidle")
                        await page.screenshot(path="screenshots/03_weather_page.png")
                        print("📸 Screenshot saved: 03_weather_page.png")

                        # Check if we got weather data
                        weather_content = page.locator(".weather-display")
                        if await weather_content.count() > 0:
                            print("✅ Weather data displayed successfully")
                        else:
                            print("❌ No weather data found")
                    else:
                        # Check if we were redirected directly to weather page
                        weather_content = page.locator(".weather-display")
                        if await weather_content.count() > 0:
                            print("✅ Redirected directly to weather page")
                        else:
                            print("❌ No weather results or location selection found")
                else:
                    print("❌ Regular search form not found")

                # Test 2: Forecast Form
                print("\n🔍 Testing forecast form")
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                forecast_form = page.locator('form[action="/forecast"]')
                location_input = forecast_form.locator('input[name="location"]')

                if await location_input.count() > 0:
                    print("✅ Forecast form found")
                    await location_input.fill("Paris")

                    forecast_button = forecast_form.locator('button[type="submit"]')
                    await forecast_button.click()

                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path="screenshots/04_forecast.png")
                    print("📸 Screenshot saved: 04_forecast.png")

                    await self.check_for_errors(page, "Forecast form")
                else:
                    print("❌ Forecast form not found")

                # Test 3: Natural Language Query
                print("\n🔍 Testing natural language queries")
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                nl_form = page.locator('form[action="/nl-date-weather"]')
                nl_input = nl_form.locator('input[name="query"]')

                if await nl_input.count() > 0:
                    print("✅ Natural language form found")
                    await nl_input.fill("What's the weather like in Tokyo tomorrow?")

                    nl_button = nl_form.locator('input[type="submit"]')
                    await nl_button.click()

                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path="screenshots/05_nl_query.png")
                    print("📸 Screenshot saved: 05_nl_query.png")

                    await self.check_for_errors(page, "Natural language query")
                else:
                    print("❌ Natural language form not found")

                # Test 4: Quick Links
                print("\n🔍 Testing quick links")
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                london_button = page.locator('button:text("London")')
                if await london_button.count() > 0:
                    print("✅ Quick links found")
                    await london_button.click()

                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path="screenshots/06_quick_link.png")
                    print("📸 Screenshot saved: 06_quick_link.png")

                    await self.check_for_errors(page, "Quick links")
                else:
                    print("❌ Quick links not found")

            except Exception as e:
                print(f"❌ Test failed with error: {e}")
                await page.screenshot(path="screenshots/error.png")
                print("📸 Error screenshot saved: error.png")

            finally:
                await browser.close()

    async def check_for_errors(self, page: Page, test_name: str):
        """Helper method to check for error messages"""
        error_messages = page.locator(".flash-message.error, .flash-message.warning")
        if await error_messages.count() > 0:
            for i in range(await error_messages.count()):
                error_text = await error_messages.nth(i).text_content()
                print(f"❌ {test_name} Error: {error_text}")
        else:
            print(f"✅ {test_name} completed without errors")

    async def test_api_connectivity(self):
        """Test API connectivity and responses"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print("\n🌐 Testing API Connectivity")

            # Capture network requests
            requests = []
            responses = []

            def handle_request(request):
                requests.append(f"Request: {request.method} {request.url}")

            def handle_response(response):
                responses.append(f"Response: {response.status} {response.url}")
                if response.status >= 400:
                    print(f"❌ HTTP Error: {response.status} {response.url}")

            page.on("request", handle_request)
            page.on("response", handle_response)

            # Enable console logging
            def handle_console(msg):
                if msg.type == "error":
                    print(f"❌ Console Error: {msg.text}")
                else:
                    print(f"Console: {msg.text}")

            page.on("console", handle_console)

            try:
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                # Check network requests
                print("📡 Network activity:")
                for response in responses:
                    print(f"  {response}")

                # Try a simple search to trigger API calls
                search_form = page.locator('form[action="/search"]')
                search_input = search_form.locator('input[name="query"]')

                if await search_input.count() > 0:
                    await search_input.fill("London")
                    search_button = search_form.locator('button[type="submit"]')
                    await search_button.click()
                    await page.wait_for_load_state("networkidle")

                    print("📡 Network activity after search:")
                    for response in responses[-5:]:  # Show last 5 responses
                        print(f"  {response}")

            except Exception as e:
                print(f"❌ API test failed: {e}")

            finally:
                await browser.close()


async def main():
    # Create screenshots directory
    import os

    os.makedirs("screenshots", exist_ok=True)

    tester = WebUITester()
    await tester.test_location_search()
    await tester.test_api_connectivity()


if __name__ == "__main__":
    asyncio.run(main())
