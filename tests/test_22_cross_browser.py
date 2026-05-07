"""Section 22 — Cross-Browser Testing

Verify that key member-facing pages render correctly in Firefox and WebKit (Safari).
Tests gracefully skip if the browser binary is unavailable (system dependencies not yet
installed — run `sudo playwright install-deps` to enable).
"""
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Page
from tests.helpers import BASE_URL, LOGIN_URL, DASHBOARD_URL, AVAILABILITY_URL, screenshot_path, ALICE, login

CROSS_BROWSER_URLS = [
    ("/", "home"),
    ("/user/sign-in/", "login"),
    ("/bookings/check_availability/", "availability"),
]


async def _make_page(browser_type_name: str):
    """Launch the named browser and return (playwright, browser, page). Skips if unavailable."""
    pw = await async_playwright().start()
    try:
        browser_type = getattr(pw, browser_type_name)
        browser = await browser_type.launch(headless=True)
    except Exception as exc:
        await pw.stop()
        pytest.skip(f"{browser_type_name} unavailable: {exc}")
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    return pw, browser, page


@pytest.mark.asyncio
@pytest.mark.parametrize("path,label", CROSS_BROWSER_URLS)
async def test_22_1_firefox_public_pages(path: str, label: str):
    """Public pages load without error in Firefox."""
    pw, browser, page = await _make_page("firefox")
    try:
        resp = await page.goto(f"{BASE_URL}{path}")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=screenshot_path(f"22_firefox_{label}"))
        status = resp.status if resp else 0
        assert status < 500, f"Firefox: {path} returned {status}"
        assert "500" not in await page.title(), f"Firefox: server error on {path}"
    finally:
        await browser.close()
        await pw.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("path,label", CROSS_BROWSER_URLS)
async def test_22_2_webkit_public_pages(path: str, label: str):
    """Public pages load without error in WebKit (Safari engine)."""
    pw, browser, page = await _make_page("webkit")
    try:
        resp = await page.goto(f"{BASE_URL}{path}")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=screenshot_path(f"22_webkit_{label}"))
        status = resp.status if resp else 0
        assert status < 500, f"WebKit: {path} returned {status}"
        assert "500" not in await page.title(), f"WebKit: server error on {path}"
    finally:
        await browser.close()
        await pw.stop()


@pytest.mark.asyncio
async def test_22_3_firefox_login_flow():
    """Alice can log in and reach the dashboard in Firefox."""
    pw, browser, page = await _make_page("firefox")
    try:
        await login(page, ALICE["email"], ALICE["password"])
        await page.goto(DASHBOARD_URL)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=screenshot_path("22_firefox_dashboard"))
        assert "500" not in await page.title(), "Firefox: server error on dashboard after login"
        content = await page.content()
        assert any(kw in content.lower() for kw in ["dashboard", "wallet", "booking", "alice"]), \
            "Firefox: dashboard missing expected content after login"
    finally:
        await browser.close()
        await pw.stop()


@pytest.mark.asyncio
async def test_22_4_webkit_login_flow():
    """Alice can log in and reach the dashboard in WebKit."""
    pw, browser, page = await _make_page("webkit")
    try:
        await login(page, ALICE["email"], ALICE["password"])
        await page.goto(DASHBOARD_URL)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=screenshot_path("22_webkit_dashboard"))
        assert "500" not in await page.title(), "WebKit: server error on dashboard after login"
        content = await page.content()
        assert any(kw in content.lower() for kw in ["dashboard", "wallet", "booking", "alice"]), \
            "WebKit: dashboard missing expected content after login"
    finally:
        await browser.close()
        await pw.stop()


@pytest.mark.asyncio
async def test_22_5_firefox_availability_search():
    """Availability search returns room results in Firefox."""
    from datetime import date, timedelta
    pw, browser, page = await _make_page("firefox")
    checkin  = (date.today() + timedelta(days=80)).strftime("%Y-%m-%d")
    checkout = (date.today() + timedelta(days=82)).strftime("%Y-%m-%d")
    try:
        await login(page, ALICE["email"], ALICE["password"])
        await page.goto(AVAILABILITY_URL)
        await page.wait_for_load_state("networkidle")
        await page.fill('input[name="check_in_date"]', checkin)
        await page.fill('input[name="check_out_date"]', checkout)
        await page.evaluate(
            'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
        )
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=screenshot_path("22_firefox_availability"))
        content = await page.content()
        assert any(kw in content.lower() for kw in ["room", "bunk", "available", "no rooms"]), \
            "Firefox: availability search returned unexpected content"
    finally:
        await browser.close()
        await pw.stop()
