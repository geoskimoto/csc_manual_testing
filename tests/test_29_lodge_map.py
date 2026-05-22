"""Section 29 — Interactive Lodge Map Booking Flow"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import AVAILABILITY_URL, CART_URL, screenshot_path

_CHECKIN_DATE  = date.today() + timedelta(days=30)
_CHECKOUT_DATE = date.today() + timedelta(days=32)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")
CHECKIN_DISPLAY  = _CHECKIN_DATE.strftime("%B %-d, %Y")
CHECKOUT_DISPLAY = _CHECKOUT_DATE.strftime("%B %-d, %Y")


async def _search_and_enter_map(page: Page) -> None:
    """Navigate to availability, search dates, toggle to map view."""
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', CHECKIN)
    await page.fill('input[name="check_out_date"]', CHECKOUT)
    await page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)
    await page.click('#view-toggle-map')
    await page.wait_for_selector('#lodge-map-host', state='visible')
    await page.wait_for_timeout(1000)


@pytest.mark.asyncio
async def test_29_1_map_view_toggle(alice_map_page: Page):
    """Clicking Map View shows the SVG host and hides the card grid."""
    await alice_map_page.screenshot(path=screenshot_path("29_1_map_toggle"))
    map_host = alice_map_page.locator('#lodge-map-host')
    assert await map_host.is_visible(), "#lodge-map-host not visible after toggling map view"
    assert "500" not in await alice_map_page.title(), "Server error on availability page"


@pytest.mark.asyncio
async def test_29_2_map_renders_rooms(alice_map_page: Page):
    """Map SVG renders at least one available room."""
    await alice_map_page.screenshot(path=screenshot_path("29_2_map_rooms"))
    rooms = alice_map_page.locator('.lm-room')
    assert await rooms.count() > 0, "No .lm-room elements found in map SVG"
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    assert await available.count() > 0, "No available rooms shown on map"


@pytest.mark.asyncio
async def test_29_3_map_legend_visible(alice_map_page: Page):
    """Map legend swatches are present."""
    await alice_map_page.screenshot(path=screenshot_path("29_3_legend"))
    swatches = alice_map_page.locator('.lm-swatch')
    count = await swatches.count()
    assert count >= 2, f"Expected at least 2 legend swatches, found {count}"


@pytest.mark.asyncio
async def test_29_4_click_room_opens_popover(alice_map_page: Page):
    """Clicking an available room reveals the popover with a room title."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')
    await alice_map_page.screenshot(path=screenshot_path("29_4_popover_open"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert await popover.is_visible(), "Popover did not appear after clicking room"

    title = alice_map_page.locator('#lodge-map-popover-title')
    title_text = await title.text_content()
    assert title_text and title_text.strip(), "Popover title is empty"


@pytest.mark.asyncio
async def test_29_6_popover_done_closes(alice_map_page: Page):
    """Done button closes the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.click('#lodge-map-popover-done')
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='hidden')
    await alice_map_page.screenshot(path=screenshot_path("29_6_done_closes"))

    assert not await alice_map_page.locator('#lodge-map-popover').is_visible(), \
        "Popover still visible after clicking Done"


@pytest.mark.asyncio
async def test_29_7_popover_x_closes(alice_map_page: Page):
    """X (close) button closes the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.click('#lodge-map-popover-close')
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='hidden')
    await alice_map_page.screenshot(path=screenshot_path("29_7_x_closes"))

    assert not await alice_map_page.locator('#lodge-map-popover').is_visible(), \
        "Popover still visible after clicking X"
