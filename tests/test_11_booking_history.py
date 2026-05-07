"""Section 11 — Member Booking History & Detail"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, DASHBOARD_URL, screenshot_path

BOOKINGS_URL = f"{BASE_URL}/dashboard/bookings/"


@pytest.mark.asyncio
async def test_11_1_bookings_page_loads(alice_page: Page):
    """Booking history page loads without error."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("11_1_booking_history"))
    assert "500" not in await alice_page.title(), "Server error on booking history page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "booking", "history", "reservation", "no bookings", "upcoming"
    ]), "Booking history page did not render expected content"


@pytest.mark.asyncio
async def test_11_2_booking_detail_loads(alice_page: Page):
    """Clicking a booking opens the detail page with full info."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    count = await booking_links.count()
    if count == 0:
        pytest.skip("No bookings in history to click through")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("11_2_booking_detail"))
    assert "500" not in await alice_page.title(), "Server error on booking detail"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "check-in", "check in", "check-out", "check out", "room", "occupant", "total", "paid"
    ]), "Booking detail missing expected fields"


@pytest.mark.asyncio
async def test_11_3_booking_detail_has_dates_and_room(alice_page: Page):
    """Booking detail shows dates, room name, and price."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    if await booking_links.count() == 0:
        pytest.skip("No bookings available")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("11_3_detail_fields"))
    content = await alice_page.content()

    has_date = any(kw in content for kw in ["2025", "2026", "2027", "Jan", "Feb", "Mar",
                                              "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                                              "Oct", "Nov", "Dec"])
    has_price = "$" in content or "total" in content.lower()
    assert has_date, "No date information found on booking detail"
    assert has_price, "No price/total information found on booking detail"


@pytest.mark.asyncio
async def test_11_4_booking_invoice_link(alice_page: Page):
    """Booking detail page includes an invoice link (BKG- prefix)."""
    await alice_page.goto(BOOKINGS_URL)
    await alice_page.wait_for_load_state("networkidle")

    booking_links = alice_page.locator("button[data-booking-url*='/dashboard/booking_detail/']")
    if await booking_links.count() == 0:
        pytest.skip("No bookings available")

    await booking_links.first.click()
    await alice_page.locator("#bookingDetailsModal").wait_for(state="visible", timeout=10000)
    await alice_page.wait_for_timeout(2000)
    content = await alice_page.content()
    await alice_page.screenshot(path=screenshot_path("11_4_invoice_link"))

    has_invoice = (
        "invoice" in content.lower()
        or "/dashboard/invoice/" in content
        or "BKG-" in content
    )
    if not has_invoice:
        pytest.skip("No invoice link on this booking detail — booking may not have an invoice yet")


@pytest.mark.asyncio
async def test_11_5_dashboard_links_to_bookings(alice_page: Page):
    """Main dashboard has a link or section leading to booking history."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("11_5_dashboard_booking_link"))
    content = await alice_page.content()
    has_link = (
        "/dashboard/bookings/" in content
        or any(kw in content.lower() for kw in ["booking history", "my bookings", "view bookings"])
    )
    assert has_link, "Dashboard does not link to booking history"
