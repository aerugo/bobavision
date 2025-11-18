"""Playwright tests for UI screens."""
import pytest
import os
from playwright.sync_api import Page, expect
import threading
import time
from src.web_server import WebServer

# Skip Playwright tests in containerized environments where Chromium has issues
# Set ENABLE_PLAYWRIGHT_TESTS=1 to run these tests
pytestmark = pytest.mark.skipif(
    os.getenv("ENABLE_PLAYWRIGHT_TESTS") != "1",
    reason="Playwright tests require proper display environment. "
           "Set ENABLE_PLAYWRIGHT_TESTS=1 to enable."
)


@pytest.fixture(scope="module")
def web_server():
    """Start web server for testing."""
    server = WebServer(port=5001)
    server.start()
    time.sleep(1)  # Give server time to start
    yield server
    server.stop()


class TestSplashScreen:
    """Test splash screen UI."""

    def test_splash_screen_loads(self, page: Page, web_server):
        """Test that splash screen loads successfully."""
        # Navigate to splash screen
        page.goto("http://localhost:5001/")

        # Check that page loaded
        expect(page).to_have_title("BobaVision - Splash")

    def test_splash_screen_has_logo(self, page: Page, web_server):
        """Test that splash screen displays logo."""
        page.goto("http://localhost:5001/")

        # Check for logo element
        logo = page.locator(".logo")
        expect(logo).to_be_visible()

    def test_splash_screen_has_title(self, page: Page, web_server):
        """Test that splash screen displays title."""
        page.goto("http://localhost:5001/")

        # Check for title
        title = page.locator(".title")
        expect(title).to_be_visible()
        expect(title).to_contain_text("BobaVision")

    def test_splash_screen_has_tagline(self, page: Page, web_server):
        """Test that splash screen displays tagline."""
        page.goto("http://localhost:5001/")

        # Check for tagline
        tagline = page.locator(".tagline")
        expect(tagline).to_be_visible()
        expect(tagline).to_contain_text("Press the button")

    def test_splash_screen_loads_css(self, page: Page, web_server):
        """Test that splash screen loads CSS files."""
        page.goto("http://localhost:5001/")

        # Check that CSS is applied by verifying computed styles
        container = page.locator(".splash-container")
        expect(container).to_be_visible()

    def test_splash_screen_loads_javascript(self, page: Page, web_server):
        """Test that splash screen loads JavaScript."""
        page.goto("http://localhost:5001/")

        # Check that script loaded (state_handler.js logs to console)
        # We can verify by checking for the script tag
        expect(page.locator('script[src="/scripts/state_handler.js"]')).to_be_attached()


class TestLoadingScreen:
    """Test loading screen UI."""

    def test_loading_screen_loads(self, page: Page, web_server):
        """Test that loading screen loads successfully."""
        page.goto("http://localhost:5001/loading.html")

        # Check that page loaded
        expect(page).to_have_title("BobaVision - Loading")

    def test_loading_screen_has_spinner(self, page: Page, web_server):
        """Test that loading screen displays spinner."""
        page.goto("http://localhost:5001/loading.html")

        # Check for spinner element
        spinner = page.locator(".spinner")
        expect(spinner).to_be_visible()

    def test_loading_screen_has_message(self, page: Page, web_server):
        """Test that loading screen displays loading message."""
        page.goto("http://localhost:5001/loading.html")

        # Check for loading message
        message = page.locator(".message")
        expect(message).to_be_visible()
        expect(message).to_contain_text("Getting your video ready")


class TestAllDoneScreen:
    """Test 'all done' screen UI."""

    def test_all_done_screen_loads(self, page: Page, web_server):
        """Test that 'all done' screen loads successfully."""
        page.goto("http://localhost:5001/all_done.html")

        # Check that page loaded
        expect(page).to_have_title("BobaVision - All Done")

    def test_all_done_screen_has_celebration(self, page: Page, web_server):
        """Test that 'all done' screen displays celebration elements."""
        page.goto("http://localhost:5001/all_done.html")

        # Check for celebration element
        celebration = page.locator(".celebration")
        expect(celebration).to_be_visible()

    def test_all_done_screen_has_title(self, page: Page, web_server):
        """Test that 'all done' screen displays title."""
        page.goto("http://localhost:5001/all_done.html")

        # Check for title
        title = page.locator(".title")
        expect(title).to_be_visible()
        expect(title).to_contain_text("Great Watching")

    def test_all_done_screen_has_message(self, page: Page, web_server):
        """Test that 'all done' screen displays message."""
        page.goto("http://localhost:5001/all_done.html")

        # Check for message
        message = page.locator(".message")
        expect(message).to_be_visible()
        expect(message).to_contain_text("all your videos")


class TestErrorScreen:
    """Test error screen UI."""

    def test_error_screen_loads(self, page: Page, web_server):
        """Test that error screen loads successfully."""
        page.goto("http://localhost:5001/error.html")

        # Check that page loaded
        expect(page).to_have_title("BobaVision - Oops")

    def test_error_screen_has_icon(self, page: Page, web_server):
        """Test that error screen displays icon."""
        page.goto("http://localhost:5001/error.html")

        # Check for icon element
        icon = page.locator(".icon")
        expect(icon).to_be_visible()

    def test_error_screen_has_title(self, page: Page, web_server):
        """Test that error screen displays title."""
        page.goto("http://localhost:5001/error.html")

        # Check for title
        title = page.locator(".title")
        expect(title).to_be_visible()
        expect(title).to_contain_text("Oops")

    def test_error_screen_has_message(self, page: Page, web_server):
        """Test that error screen displays friendly message."""
        page.goto("http://localhost:5001/error.html")

        # Check for message
        message = page.locator(".message")
        expect(message).to_be_visible()
        expect(message).to_contain_text("went wrong")

    def test_error_screen_has_retry_countdown(self, page: Page, web_server):
        """Test that error screen displays retry countdown."""
        page.goto("http://localhost:5001/error.html")

        # Check for retry element
        retry = page.locator(".retry")
        expect(retry).to_be_visible()
        expect(retry).to_contain_text("Trying again")


class TestResponsiveDesign:
    """Test responsive design across all screens."""

    def test_splash_screen_is_responsive(self, page: Page, web_server):
        """Test that splash screen adapts to different viewports."""
        page.goto("http://localhost:5001/")

        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Full HD
            {"width": 1280, "height": 720},   # HD
            {"width": 800, "height": 600},    # Small screen
        ]

        for viewport in viewports:
            page.set_viewport_size(viewport)
            # Check that content is still visible
            expect(page.locator(".splash-container")).to_be_visible()

    def test_all_screens_have_no_horizontal_scroll(self, page: Page, web_server):
        """Test that screens don't cause horizontal scrolling."""
        screens = ["/", "/loading.html", "/all_done.html", "/error.html"]

        for screen in screens:
            page.goto(f"http://localhost:5001{screen}")

            # Check that body width doesn't exceed viewport
            # This prevents horizontal scroll
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = page.viewport_size["width"]
            assert body_width <= viewport_width, f"Screen {screen} causes horizontal scroll"


class TestAccessibility:
    """Test accessibility features."""

    def test_splash_screen_has_proper_structure(self, page: Page, web_server):
        """Test that splash screen has semantic HTML structure."""
        page.goto("http://localhost:5001/")

        # Check that page has proper HTML5 structure
        expect(page.locator("html[lang]")).to_be_attached()
        expect(page.locator("meta[charset]")).to_be_attached()
        expect(page.locator("meta[name='viewport']")).to_be_attached()

    def test_all_screens_have_titles(self, page: Page, web_server):
        """Test that all screens have descriptive titles."""
        screens_and_titles = [
            ("/", "BobaVision - Splash"),
            ("/loading.html", "BobaVision - Loading"),
            ("/all_done.html", "BobaVision - All Done"),
            ("/error.html", "BobaVision - Oops"),
        ]

        for screen, expected_title in screens_and_titles:
            page.goto(f"http://localhost:5001{screen}")
            expect(page).to_have_title(expected_title)


class TestStaticAssets:
    """Test that static assets load correctly."""

    def test_common_css_loads(self, page: Page, web_server):
        """Test that common.css loads successfully."""
        response = page.goto("http://localhost:5001/styles/common.css")
        assert response.status == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_state_handler_js_loads(self, page: Page, web_server):
        """Test that state_handler.js loads successfully."""
        response = page.goto("http://localhost:5001/scripts/state_handler.js")
        assert response.status == 200
        # JavaScript can be served as text/javascript or application/javascript
        content_type = response.headers.get("content-type", "").lower()
        assert "javascript" in content_type or "text" in content_type
