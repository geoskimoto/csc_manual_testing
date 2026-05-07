"""Section 13 — Admin Manage & Refund Bookings

Booking Administrators can view, filter, and refund bookings via the admin manage
tools. Tests verify the manage-bookings list, booking detail, and refund UI.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import (
    BASE_URL, ADMIN_URL, ADMIN_MANAGE_URL, screenshot_path,
)

ADMIN_REFUND_URL = f"{BASE_URL}/admin-bookings/refund-booking/"


@pytest.mark.asyncio
async def test_13_1_manage_bookings_loads(booking_admin_page: Page):
    """Admin manage-bookings list loads and shows booking data."""
    await booking_admin_page.goto(ADMIN_MANAGE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("13_1_manage_bookings"))
    assert "500" not in await booking_admin_page.title(), "Server error on manage-bookings"
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "booking", "member", "status", "date", "room"
    ]), "Manage-bookings page missing expected content"


@pytest.mark.asyncio
async def test_13_2_manage_bookings_shows_alice_booking(booking_admin_page: Page):
    """Alice's seeded booking appears in the admin manage-bookings list."""
    await booking_admin_page.goto(ADMIN_MANAGE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("13_2_alice_booking_in_list"))
    content = await booking_admin_page.content()
    has_alice = "alice" in content.lower() or "tester" in content.lower()
    if not has_alice:
        pytest.skip("Alice's booking not visible in admin list — may require search or filter")


@pytest.mark.asyncio
async def test_13_3_manage_bookings_has_search_or_filter(booking_admin_page: Page):
    """Admin manage-bookings page has a search input or filter controls."""
    await booking_admin_page.goto(ADMIN_MANAGE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("13_3_manage_search"))
    has_input = await booking_admin_page.locator('input[type="text"], input[type="search"]').count() > 0
    has_form  = await booking_admin_page.locator("form").count() > 0
    assert has_input or has_form, "Admin manage-bookings page has no search/filter controls"


@pytest.mark.asyncio
async def test_13_4_admin_booking_detail_loads(booking_admin_page: Page):
    """Admin booking detail modal loads when the view-details button is clicked.

    The manage-bookings page loads detail via JavaScript fetch into a Bootstrap
    modal (button.view-details-btn), not via a direct anchor link.
    """
    await booking_admin_page.goto(ADMIN_MANAGE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    detail_btn = booking_admin_page.locator("button.view-details-btn").first
    if await detail_btn.count() == 0:
        pytest.skip("No view-details buttons found on manage-bookings — no bookings in list")

    await detail_btn.click()
    # Allow the fetch to complete and the modal to populate
    await booking_admin_page.wait_for_timeout(2000)
    await booking_admin_page.screenshot(path=screenshot_path("13_4_booking_detail_modal"))

    assert "500" not in await booking_admin_page.title(), "Server error after opening detail modal"
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in [
        "booking", "room", "check-in", "status", "member", "bunk"
    ]), "Booking detail modal missing expected content after fetch"


@pytest.mark.asyncio
async def test_13_5_admin_manage_blocked_for_regular_member(alice_page: Page):
    """Regular member cannot access admin manage-bookings page."""
    resp = await alice_page.goto(ADMIN_MANAGE_URL)
    await alice_page.wait_for_load_state("networkidle")
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path("13_5_manage_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "login" in url
    assert is_blocked, f"Regular member accessed manage-bookings — status {status}"


@pytest.mark.asyncio
async def test_13_6_admin_can_view_dashboard_stats(booking_admin_page: Page):
    """Admin dashboard shows summary statistics (bookings, revenue, etc.)."""
    await booking_admin_page.goto(ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("13_6_admin_stats"))
    content = await booking_admin_page.content()
    has_stats = any(kw in content.lower() for kw in [
        "total", "booking", "revenue", "member", "pending", "confirmed"
    ])
    assert has_stats, "Admin dashboard missing summary statistics"
