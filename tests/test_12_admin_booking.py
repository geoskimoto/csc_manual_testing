"""Section 12 — Admin Booking Flow

Booking Administrators can create bookings on behalf of members via the admin booking
tools at /admin-bookings/. Tests verify the admin dashboard, member search, availability
search, cart, and checkout surfaces load correctly for a booking_admin user.
"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import (
    BASE_URL, ADMIN_URL, ADMIN_MANAGE_URL, ADMIN_AVAIL_URL,
    ADMIN_CART_URL, ADMIN_CHECKOUT_URL, ADMIN_TXNS_URL, ADMIN_SEARCH_URL,
    screenshot_path,
)

_CHECKIN_DATE  = date.today() + timedelta(days=70)
_CHECKOUT_DATE = date.today() + timedelta(days=72)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")


@pytest.mark.asyncio
async def test_12_1_admin_dashboard_loads(booking_admin_page: Page):
    """Admin booking dashboard is reachable for a booking_admin user."""
    await booking_admin_page.goto(ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_1_admin_dashboard"))
    assert "500" not in await booking_admin_page.title(), "Server error on admin dashboard"
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "admin", "booking", "dashboard", "manage"
    ]), "Admin dashboard missing expected content"


@pytest.mark.asyncio
async def test_12_2_admin_blocked_for_regular_member(alice_page: Page):
    """Regular member cannot access admin booking dashboard."""
    resp = await alice_page.goto(ADMIN_URL)
    await alice_page.wait_for_load_state("networkidle")
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path("12_2_admin_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "login" in url or "403" in url
    assert is_blocked, f"Regular member accessed admin dashboard — status {status}, url {url}"


@pytest.mark.asyncio
async def test_12_3_admin_availability_search(booking_admin_page: Page):
    """Admin can reach the availability search page."""
    await booking_admin_page.goto(ADMIN_AVAIL_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_3_admin_avail"))
    assert "500" not in await booking_admin_page.title(), "Server error on admin availability"
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "availability", "check-in", "check in", "date", "search"
    ]), "Admin availability page missing expected content"


@pytest.mark.asyncio
async def test_12_4_admin_availability_returns_results(booking_admin_page: Page):
    """Admin availability search returns room results for future dates."""
    await booking_admin_page.goto(ADMIN_AVAIL_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    date_inputs = booking_admin_page.locator('input[type="date"], input[name*="check_in"], input[name*="checkin"]')
    if await date_inputs.count() < 2:
        pytest.skip("Could not find date inputs on admin availability page")

    await date_inputs.first.fill(CHECKIN)
    await date_inputs.nth(1).fill(CHECKOUT)

    submit = booking_admin_page.locator('button[type="submit"], input[type="submit"]').first
    await submit.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.wait_for_timeout(2000)
    await booking_admin_page.screenshot(path=screenshot_path("12_4_admin_avail_results"))
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "room", "bunk", "available", "member", "add"
    ]), "Admin availability search returned no room results"


@pytest.mark.asyncio
async def test_12_5_admin_search_members_api(booking_admin_page: Page):
    """Admin member search API responds with JSON for a known member name."""
    await booking_admin_page.goto(ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    resp = await booking_admin_page.goto(f"{ADMIN_SEARCH_URL}?q=alice")
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_5_search_members"))
    status = resp.status if resp else 0
    assert status == 200, f"Member search API returned {status}"
    content = await booking_admin_page.content()
    assert "alice" in content.lower() or "tester" in content.lower() or "[" in content, \
        "Member search API did not return Alice's profile"


@pytest.mark.asyncio
async def test_12_6_admin_cart_page_loads(booking_admin_page: Page):
    """Admin cart page loads without error."""
    await booking_admin_page.goto(ADMIN_CART_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_6_admin_cart"))
    assert "500" not in await booking_admin_page.title(), "Server error on admin cart page"


@pytest.mark.asyncio
async def test_12_7_admin_checkout_page_loads(booking_admin_page: Page):
    """Admin checkout page loads without error (may show empty cart)."""
    await booking_admin_page.goto(ADMIN_CHECKOUT_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_7_admin_checkout"))
    assert "500" not in await booking_admin_page.title(), "Server error on admin checkout page"


@pytest.mark.asyncio
async def test_12_8_admin_transactions_page_loads(booking_admin_page: Page):
    """Admin transactions history page loads without error."""
    await booking_admin_page.goto(ADMIN_TXNS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("12_8_admin_transactions"))
    assert "500" not in await booking_admin_page.title(), "Server error on admin transactions page"
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "transaction", "payment", "booking", "history", "amount"
    ]), "Admin transactions page missing expected content"
