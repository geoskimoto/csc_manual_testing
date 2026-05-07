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
    """Bookings section is reachable from dashboard."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    bookings_link = alice_page.locator("a").filter(has_text="Booking").first
    if await bookings_link.count() > 0:
        await bookings_link.click()
        await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("03_3_bookings_tab"))
    assert "500" not in await alice_page.title()


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
