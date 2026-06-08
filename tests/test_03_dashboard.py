"""Section 3 — Member Dashboard"""
import pytest
from playwright.async_api import Page
from tests.helpers import DASHBOARD_URL, PROFILE_URL, WALLET_URL, screenshot_path


@pytest.mark.asyncio
async def test_3_1_dashboard_loads(alice_page: Page):
    """Dashboard overview is accessible after login."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("03_1_dashboard"))
    assert "/dashboard" in alice_page.url, f"Unexpected URL: {alice_page.url}"


@pytest.mark.asyncio
async def test_3_2_dashboard_shows_wallet(alice_page: Page):
    """Dashboard shows a dollar amount (wallet balance)."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    content = await alice_page.content()
    assert "$" in content, "No dollar sign found — wallet balance may be missing"
    await alice_page.screenshot(path=screenshot_path("03_2_wallet_balance"))


@pytest.mark.asyncio
async def test_3_3_bookings_tab(alice_page: Page):
    """Bookings section is reachable from dashboard.

    The dashboard does not have a named 'Bookings' nav tab — the booking flow
    is reached via the 'Make a Booking' CTA or direct URL.  This test verifies
    the availability/check-in page loads for Alice (i.e. she has booking access).
    """
    from tests.helpers import AVAILABILITY_URL
    await alice_page.goto(AVAILABILITY_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("03_3_bookings_tab"))
    assert "500" not in await alice_page.title()
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["check in", "check-in", "availability", "date"]), \
        "Availability page did not render — Alice may lack booking access"


@pytest.mark.asyncio
async def test_3_4_profile_page(alice_page: Page):
    """Profile page loads and shows Alice's name."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("03_4_profile"))
    content = await alice_page.content()
    assert "alice" in content.lower() or "tester" in content.lower(), \
        "Profile page does not show Alice's name"


@pytest.mark.asyncio
async def test_3_5_wallet_page(alice_page: Page):
    """Wallet page loads and shows balance."""
    await alice_page.goto(WALLET_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("03_5_wallet"))
    content = await alice_page.content()
    assert "$" in content, "No balance shown on wallet page"
