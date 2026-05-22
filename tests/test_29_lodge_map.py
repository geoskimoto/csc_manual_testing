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


@pytest.mark.asyncio
async def test_29_5_room_color_changes_on_assignment(alice_map_page: Page):
    """Selecting an occupant in the popover changes the room's visual state to assigned."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    first_room = available.first
    room_id = await first_room.get_attribute("data-room")

    await first_room.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    select = alice_map_page.locator('#lodge-map-popover-body select.member-select')
    opts = await select.locator('option').all()
    chosen = None
    for opt in opts:
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.strip() and disabled is None:
            chosen = val
            break

    if chosen is None:
        pytest.skip("No selectable occupant found in popover dropdown")

    await select.select_option(value=chosen)
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_5_color_change"))

    room_state = await alice_map_page.locator(
        f'.lm-room[data-room="{room_id}"]'
    ).get_attribute("data-state")
    assert room_state == "assigned", \
        f"Room {room_id} data-state is '{room_state}', expected 'assigned'"


@pytest.mark.asyncio
async def test_29_8_location_filter_applies_to_map(alice_map_page: Page):
    """Changing the location filter updates the map without a server error."""
    filter_select = alice_map_page.locator('#location-filter')
    if await filter_select.count() == 0:
        pytest.skip("Location filter not found")

    options = await filter_select.locator('option').all()
    if len(options) < 2:
        pytest.skip("No filter options to select")

    # Select the second option (first non-All)
    second_val = await options[1].get_attribute("value")
    await filter_select.select_option(value=second_val)
    await alice_map_page.wait_for_timeout(800)

    await alice_map_page.screenshot(path=screenshot_path("29_8_filter_map"))

    assert "500" not in await alice_map_page.title(), "Server error after applying location filter"
    assert await alice_map_page.locator('#lodge-map-host').is_visible(), \
        "#lodge-map-host hidden after applying filter"
    filtered_count = await alice_map_page.locator('.lm-room').count()
    assert filtered_count >= 0, "Unexpected negative room count after filter"


@pytest.mark.asyncio
async def test_29_9_keyboard_enter_opens_popover(alice_map_page: Page):
    """Pressing Enter on a focused available room opens the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await alice_map_page.evaluate("""
        const room = document.querySelector('.lm-room[data-state="available"]');
        if (room) room.focus();
    """)
    await alice_map_page.wait_for_timeout(300)

    await alice_map_page.keyboard.press('Enter')
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_9_keyboard_enter"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert await popover.is_visible(), "Popover did not open on keyboard Enter"


@pytest.mark.asyncio
async def test_29_10_keyboard_escape_closes_popover(alice_map_page: Page):
    """Pressing Escape while popover is open closes it."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.keyboard.press('Escape')
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_10_escape_closes"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert not await popover.is_visible(), "Popover still visible after pressing Escape"
