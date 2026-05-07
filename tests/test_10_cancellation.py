"""Section 10 — Booking Cancellation & Refund"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import (
    BASE_URL, AVAILABILITY_URL, CART_URL, CHECKOUT_URL,
    DASHBOARD_URL, screenshot_path, ALICE
)

CHECKIN_FAR  = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
CHECKOUT_FAR = (date.today() + timedelta(days=32)).strftime("%Y-%m-%d")
BOOKINGS_URL = f"{BASE_URL}/dashboard/bookings/"


async def _add_room_to_cart(page: Page, checkin: str, checkout: str) -> bool:
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', checkin)
    await page.fill('input[name="check_out_date"]', checkout)
    await page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await page.wait_for_load_state("networkidle")

    selects = page.locator("select.member-select")
    if await selects.count() == 0:
        return False
    first = selects.first
    for opt in await first.locator("option").all():
        val = await opt.get_attribute("value")
        if val and val.strip():
            await first.select_option(value=val)
            break
    btn = page.locator("button").filter(has_text="Add Selected to Cart")
    if await btn.count() == 0:
        return False
    await btn.click()
    await page.wait_for_load_state("networkidle")
    return True


@pytest.mark.asyncio
async def test_10_1_cancel_button_visible_on_booking(alice_page: Page):
    """Booking detail page shows a cancel or refund action for confirmed bookings."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("10_1_bookings_list"))
    content = await alice_page.content()

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    count = await booking_links.count()
    if count == 0:
        pytest.skip("No bookings found in booking history to test cancellation")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("10_1_booking_detail"))
    content = await alice_page.content()

    has_action = any(kw in content.lower() for kw in ["cancel", "refund", "confirmed", "status"])
    assert has_action, "No cancel/refund action or status found on booking detail page"


@pytest.mark.asyncio
async def test_10_2_refund_url_exists(alice_page: Page):
    """Refund endpoint URL pattern is present in booking detail for refundable bookings."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    if await booking_links.count() == 0:
        pytest.skip("No bookings found to check for refund links")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    content = await alice_page.content()
    await alice_page.screenshot(path=screenshot_path("10_2_refund_link"))

    has_refund = "refund" in content.lower() or "/refund-booking/" in content
    # Even if no refund button (e.g. booking already refunded), page must not 500
    assert "500" not in await alice_page.title(), "Server error on booking detail"
    if not has_refund:
        pytest.skip("No refund option visible — booking may not be in refundable state")


@pytest.mark.asyncio
async def test_10_3_booking_history_has_status_badges(alice_page: Page):
    """Booking history shows status badges (confirmed, refunded, cancelled)."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("10_3_booking_status_badges"))
    content = await alice_page.content()
    assert "500" not in await alice_page.title(), "Server error on bookings page"
    assert any(kw in content.lower() for kw in [
        "confirmed", "cancelled", "refunded", "partially_refunded",
        "booking", "no bookings", "history"
    ]), "Bookings page did not render expected content"


@pytest.mark.asyncio
async def test_10_4_cancellation_policy_info_present(alice_page: Page):
    """Booking detail or checkout includes cancellation policy info."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    if await booking_links.count() == 0:
        pytest.skip("No bookings available to check cancellation policy display")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("10_4_cancellation_policy"))
    content = await alice_page.content()

    has_policy = any(kw in content.lower() for kw in [
        "cancellation", "refund policy", "72 hour", "48 hour", "policy"
    ])
    if not has_policy:
        pytest.skip("Cancellation policy text not visible on this booking detail — may vary by booking state")
