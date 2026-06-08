"""Section 30 — Bed List Calendar with Occupancy Map View"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import BED_LIST_URL, LOGIN_URL, BASE_URL, screenshot_path


@pytest.mark.asyncio
async def test_30_1_bed_list_page_loads(alice_page: Page):
    """Bed list calendar page loads without a server error."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("30_1_bed_list_load"))
    assert "500" not in await alice_page.title(), "Server error on bed list calendar page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["calendar", "bed", "lodge", "occupancy"]), \
        "Bed list page did not render expected content"


@pytest.mark.asyncio
async def test_30_2_calendar_renders(alice_page: Page):
    """FullCalendar grid renders on the bed list page."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)  # FullCalendar initialisation
    await alice_page.screenshot(path=screenshot_path("30_2_calendar"))

    # FullCalendar adds .fc to the root element
    fc = alice_page.locator('.fc')
    assert await fc.count() > 0, "FullCalendar .fc element not found on bed list page"


@pytest.mark.asyncio
async def test_30_3_click_date_shows_bookings(alice_page: Page):
    """Clicking a calendar date fetches and displays the booking list for that date."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    # Click today's date cell — FullCalendar marks it with .fc-day-today
    today_cell = alice_page.locator('.fc-day-today')
    if await today_cell.count() == 0:
        pytest.skip("Today's date cell not found in FullCalendar grid")

    await today_cell.first.click()
    await alice_page.wait_for_timeout(1500)
    await alice_page.screenshot(path=screenshot_path("30_3_date_clicked"))

    # The booking details container should become visible
    container = alice_page.locator('#booking-details-container')
    assert await container.is_visible(), \
        "#booking-details-container not visible after clicking a date"


@pytest.mark.asyncio
async def test_30_4_card_map_toggle_appears(alice_page: Page):
    """After clicking a date, Card/Map toggle buttons appear."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    today_cell = alice_page.locator('.fc-day-today')
    if await today_cell.count() == 0:
        pytest.skip("Today's date cell not found in FullCalendar grid")

    await today_cell.first.click()
    await alice_page.wait_for_timeout(1500)
    await alice_page.screenshot(path=screenshot_path("30_4_toggle_buttons"))

    card_btn = alice_page.locator('#bl-view-card')
    map_btn  = alice_page.locator('#bl-view-map')
    assert await card_btn.is_visible(), "#bl-view-card toggle button not visible after date click"
    assert await map_btn.is_visible(),  "#bl-view-map toggle button not visible after date click"


@pytest.mark.asyncio
async def test_30_5_map_toggle_renders_svg(alice_page: Page):
    """Clicking Map view renders the SVG occupancy map."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    today_cell = alice_page.locator('.fc-day-today')
    if await today_cell.count() == 0:
        pytest.skip("Today's date cell not found in FullCalendar grid")

    await today_cell.first.click()
    await alice_page.wait_for_timeout(1500)

    map_btn = alice_page.locator('#bl-view-map')
    if not await map_btn.is_visible():
        pytest.skip("Map toggle button not visible after date click")

    await map_btn.click()
    await alice_page.wait_for_timeout(1500)
    await alice_page.screenshot(path=screenshot_path("30_5_map_view"))

    map_canvas = alice_page.locator('#bl-map-canvas')
    assert await map_canvas.is_visible(), "#bl-map-canvas not visible after switching to map view"

    svg = alice_page.locator('#bl-map-canvas svg')
    assert await svg.count() > 0, "No SVG rendered inside #bl-map-canvas"


@pytest.mark.asyncio
async def test_30_6_map_renders_room_rects(alice_page: Page):
    """The occupancy map SVG contains room elements."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    today_cell = alice_page.locator('.fc-day-today')
    if await today_cell.count() == 0:
        pytest.skip("Today's date cell not found")

    await today_cell.first.click()
    await alice_page.wait_for_timeout(1500)

    map_btn = alice_page.locator('#bl-view-map')
    if not await map_btn.is_visible():
        pytest.skip("Map toggle not visible")

    await map_btn.click()
    await alice_page.wait_for_timeout(1500)
    await alice_page.screenshot(path=screenshot_path("30_6_map_rooms"))

    rooms = alice_page.locator('#bl-map-canvas .lm-room')
    count = await rooms.count()
    assert count > 0, f"No .lm-room elements found in bed-list map SVG (got {count})"


@pytest.mark.asyncio
async def test_30_7_card_view_returns_from_map(alice_page: Page):
    """Switching back to Card view from Map view restores the booking list."""
    await alice_page.goto(BED_LIST_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    today_cell = alice_page.locator('.fc-day-today')
    if await today_cell.count() == 0:
        pytest.skip("Today's date cell not found")

    await today_cell.first.click()
    await alice_page.wait_for_timeout(1500)

    map_btn  = alice_page.locator('#bl-view-map')
    card_btn = alice_page.locator('#bl-view-card')
    if not await map_btn.is_visible():
        pytest.skip("Toggle buttons not visible")

    await map_btn.click()
    await alice_page.wait_for_timeout(1000)
    await card_btn.click()
    await alice_page.wait_for_timeout(800)
    await alice_page.screenshot(path=screenshot_path("30_7_back_to_card"))

    container = alice_page.locator('#booking-details-container')
    assert await container.is_visible(), \
        "#booking-details-container not visible after switching back to card view"


@pytest.mark.asyncio
async def test_30_8_unauthenticated_redirect(page: Page):
    """Unauthenticated users are redirected away from the bed list page."""
    await page.goto(BED_LIST_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("30_8_unauth"))
    assert BED_LIST_URL not in page.url or "sign-in" in page.url or "login" in page.url, \
        "Unauthenticated user was not redirected from bed list page"
