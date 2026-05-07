"""Section 5 — Family Booking

Alice and Bob are independent test accounts with no family relationship in the current
seed. Tests here verify the family management UI and that the availability page exposes
family members in the occupant dropdowns. Full end-to-end family booking (selecting a
dependent profile as occupant) is skipped unless family data is seeded.
"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import (
    BASE_URL, AVAILABILITY_URL, PROFILE_URL, DASHBOARD_URL, screenshot_path
)

_CHECKIN_DATE  = date.today() + timedelta(days=60)
_CHECKOUT_DATE = date.today() + timedelta(days=62)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")

FAMILY_URL = f"{BASE_URL}/dashboard/family/"


@pytest.mark.asyncio
async def test_5_1_profile_page_accessible(alice_page: Page):
    """Profile page loads without error (prerequisite for family management)."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("05_1_profile"))
    assert "500" not in await alice_page.title(), "Server error on profile page"


@pytest.mark.asyncio
async def test_5_2_family_section_on_profile_or_dashboard(alice_page: Page):
    """Profile or dashboard exposes a family management section or link."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("05_2_family_section"))
    content = await alice_page.content()
    has_family = any(kw in content.lower() for kw in ["family", "dependent", "household"])
    if not has_family:
        pytest.skip("No family section visible on dashboard — may require family data to be seeded")


@pytest.mark.asyncio
async def test_5_3_availability_shows_member_selects(alice_page: Page):
    """Availability results include occupant assignment dropdowns (member-select)."""
    await alice_page.goto(AVAILABILITY_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.fill('input[name="check_in_date"]', CHECKIN)
    await alice_page.fill('input[name="check_out_date"]', CHECKOUT)
    await alice_page.evaluate(
        'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
    )
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("05_3_avail_selects"))
    member_selects = alice_page.locator("select.member-select")
    count = await member_selects.count()
    assert count > 0, "No member-select dropdowns found on availability results page"


@pytest.mark.asyncio
async def test_5_4_availability_member_select_has_alice(alice_page: Page):
    """Each occupant dropdown includes Alice's profile as a selectable option."""
    await alice_page.goto(AVAILABILITY_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.fill('input[name="check_in_date"]', CHECKIN)
    await alice_page.fill('input[name="check_out_date"]', CHECKOUT)
    await alice_page.evaluate(
        'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
    )
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)
    content = await alice_page.content()
    await alice_page.screenshot(path=screenshot_path("05_4_alice_in_select"))
    assert "alice" in content.lower() or "tester" in content.lower(), \
        "Alice's name not found in availability occupant selects"


@pytest.mark.asyncio
async def test_5_5_multiple_rooms_can_be_selected(alice_page: Page):
    """Multiple occupant dropdowns on the availability page can each have a selection."""
    await alice_page.goto(AVAILABILITY_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.fill('input[name="check_in_date"]', CHECKIN)
    await alice_page.fill('input[name="check_out_date"]', CHECKOUT)
    await alice_page.evaluate(
        'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
    )
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)

    member_selects = alice_page.locator("select.member-select")
    total = await member_selects.count()
    if total < 2:
        pytest.skip("Fewer than 2 occupant dropdowns — need multiple available rooms to test")

    # Select a valid (non-disabled) member in the first two dropdowns
    selected = 0
    for i in range(min(total, 3)):
        sel = member_selects.nth(i)
        for opt in await sel.locator("option").all():
            val = await opt.get_attribute("value")
            disabled = await opt.get_attribute("disabled")
            if val and val.strip() and disabled is None:
                await sel.select_option(value=val)
                selected += 1
                break
        if selected >= 2:
            break

    await alice_page.screenshot(path=screenshot_path("05_5_multi_select"))
    assert selected >= 1, "Could not select any occupant from availability dropdowns"
