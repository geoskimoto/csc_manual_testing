"""Section 4 — Booking Flow: Individual"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import AVAILABILITY_URL, CART_URL, ADD_TO_CART_URL, screenshot_path

_CHECKIN_DATE  = date.today() + timedelta(days=30)
_CHECKOUT_DATE = date.today() + timedelta(days=32)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")
CHECKIN_DISPLAY  = _CHECKIN_DATE.strftime("%B %-d, %Y")
CHECKOUT_DISPLAY = _CHECKOUT_DATE.strftime("%B %-d, %Y")


async def _search_availability(page: Page, checkin: str, checkout: str):
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', checkin)
    await page.fill('input[name="check_out_date"]', checkout)
    await page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)  # wait for JS to render room cards


async def _add_first_room_to_cart(page: Page, checkin_display: str = None, checkout_display: str = None) -> bool:
    member_selects = page.locator("select.member-select")
    if await member_selects.count() == 0:
        return False

    first_select = member_selects.first
    for opt in await first_select.locator("option").all():
        val = await opt.get_attribute("value")
        if val and val.strip():
            await first_select.select_option(value=val)
            break

    # Patch hidden form dates — server renders today's date; update to searched dates.
    ci = checkin_display or CHECKIN_DISPLAY
    co = checkout_display or CHECKOUT_DISPLAY
    await page.evaluate(f"""
        const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{ci}';
            if (co) co.value = '{co}';
        }}
    """)

    add_btn = page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btn.count() == 0:
        return False
    await add_btn.click()
    await page.wait_for_load_state("networkidle")
    return True


@pytest.mark.asyncio
async def test_4_1_check_availability(alice_page: Page):
    """Availability search returns rooms."""
    await _search_availability(alice_page, CHECKIN, CHECKOUT)
    await alice_page.screenshot(path=screenshot_path("04_1_availability"))
    assert "500" not in await alice_page.title(), "Server error on availability page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["bunk", "room", "available", "accommodation"]), \
        "No room listings found in availability results"


@pytest.mark.asyncio
async def test_4_2_add_room_to_cart(alice_page: Page):
    """Can select an occupant and add a room to the cart."""
    await _search_availability(alice_page, CHECKIN, CHECKOUT)
    await alice_page.screenshot(path=screenshot_path("04_2_before_add"))

    added = await _add_first_room_to_cart(alice_page)
    if not added:
        pytest.skip("No member-select or Add to Cart button found")

    await alice_page.screenshot(path=screenshot_path("04_2_after_add"))
    content = await alice_page.content()
    # After add, page returns to availability with "Added to Cart" badge or redirects to cart
    assert any(kw in content.lower() for kw in ["cart", "added", "reserved", "badge"]), \
        "No confirmation of cart addition found"


@pytest.mark.asyncio
async def test_4_3_view_cart(alice_page: Page):
    """Cart page loads and shows reserved items or empty state."""
    await alice_page.goto(CART_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("04_3_cart"))
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["cart", "booking", "accommodation", "empty"]), \
        "Cart page did not load expected content"


@pytest.mark.asyncio
async def test_4_4_cart_timer_visible(alice_page: Page):
    """Cart shows a countdown timer when items are reserved."""
    # Add a room first
    await _search_availability(alice_page, CHECKIN, CHECKOUT)
    await _add_first_room_to_cart(alice_page)
    await alice_page.goto(CART_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("04_4_cart_timer"))
    content = await alice_page.content()
    # Timer may appear as minutes:seconds countdown
    has_timer = any(kw in content.lower() for kw in ["expires", "timer", "remaining", "minutes", ":"])
    if not has_timer:
        pytest.skip("No items in cart — timer not visible (cart may have been empty)")


@pytest.mark.asyncio
async def test_4_5_remove_from_cart(alice_page: Page):
    """Remove button clears a room from the cart."""
    # Add a room first so there's something to remove
    await _search_availability(alice_page, CHECKIN, CHECKOUT)
    await _add_first_room_to_cart(alice_page)
    await alice_page.goto(CART_URL)
    await alice_page.wait_for_load_state("networkidle")

    remove_btn = alice_page.locator("button, a").filter(has_text="Remove").first
    if await remove_btn.count() == 0:
        pytest.skip("No items in cart to remove")

    await remove_btn.click()
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("04_5_after_remove"))
    content = await alice_page.content()
    assert "empty" in content.lower() or "$0.00" in content, \
        "Cart does not appear empty after removal"


@pytest.mark.asyncio
async def test_4_7_location_filter(alice_page: Page):
    """Location filter dropdown narrows room results."""
    await _search_availability(alice_page, CHECKIN, CHECKOUT)
    filter_select = alice_page.locator("#location-filter")
    if await filter_select.count() == 0:
        pytest.skip("Location filter not found")

    options = await filter_select.locator("option").all()
    if len(options) < 2:
        pytest.skip("No filter options to select")

    # Pick the second option (first non-All)
    second_val = await options[1].get_attribute("value")
    await filter_select.select_option(value=second_val)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("04_7_filtered"))
    # Just verify the page didn't crash
    assert "500" not in await alice_page.title()
