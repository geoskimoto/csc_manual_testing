"""Section 25 — Admin Transactions: Tab Switching and Invoice Filter Chips

Tests the tab navigation and the SUB/BKG/INV invoice type filter chips added to the
Invoice Payments tab of the All Transactions admin tool.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import ADMIN_TXNS_URL, LOGIN_URL, screenshot_path

BOOKINGS_TAB_URL = f"{ADMIN_TXNS_URL}?tab=bookings"
INVOICES_TAB_URL = f"{ADMIN_TXNS_URL}?tab=invoices"


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_25_1_transactions_loads_for_financial_admin(financial_admin_page: Page):
    """Transactions page loads for Financial Admin (200)."""
    response = await financial_admin_page.goto(ADMIN_TXNS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("25_1_fa_transactions"))
    assert response.status == 200
    content = await financial_admin_page.content()
    assert "Transaction" in content


@pytest.mark.asyncio
async def test_25_2_transactions_loads_for_booking_admin(booking_admin_page: Page):
    """Transactions page loads for Booking Admin (200)."""
    response = await booking_admin_page.goto(ADMIN_TXNS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("25_2_ba_transactions"))
    assert response.status == 200


@pytest.mark.asyncio
async def test_25_3_member_cannot_access(alice_page: Page):
    """Regular member receives 403 or redirect when accessing transactions page."""
    resp = await alice_page.goto(ADMIN_TXNS_URL)
    await alice_page.wait_for_load_state("networkidle")
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path("25_3_member_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "login" in url or "403" in url
    assert is_blocked, f"Regular member accessed transactions page — status {status}, url {url}"


# ---------------------------------------------------------------------------
# Tab navigation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_25_4_both_tab_links_present(financial_admin_page: Page):
    """Both 'Booking Transactions' and 'Invoice Payments' tabs are present."""
    await financial_admin_page.goto(ADMIN_TXNS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("25_4_tabs"))
    assert "tab=bookings" in content or "Booking Transactions" in content
    assert "tab=invoices" in content or "Invoice Payments" in content


@pytest.mark.asyncio
async def test_25_5_bookings_tab_shows_table(financial_admin_page: Page):
    """Bookings tab loads a table or empty state without errors."""
    await financial_admin_page.goto(BOOKINGS_TAB_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("25_5_bookings_tab"))
    content = await financial_admin_page.content()
    assert "500" not in await financial_admin_page.title()
    assert "Booking" in content or "Transaction" in content


@pytest.mark.asyncio
async def test_25_6_invoices_tab_shows_filter_chips(financial_admin_page: Page):
    """Invoice Payments tab shows all four type filter chips."""
    await financial_admin_page.goto(INVOICES_TAB_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("25_6_invoice_chips"))
    assert "SUB" in content, "SUB chip missing"
    assert "BKG" in content, "BKG chip missing"
    assert "INV" in content, "INV chip missing"
    assert "Memberships" in content
    assert "Bookings" in content
    assert "Custom" in content


# ---------------------------------------------------------------------------
# Filter chip behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_25_7_sub_chip_filters_to_subscription_invoices(financial_admin_page: Page):
    """Clicking the SUB chip adds invoice_type=subscription to the URL."""
    await financial_admin_page.goto(INVOICES_TAB_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    sub_chip = financial_admin_page.locator("a.btn", has_text="SUB").first
    await sub_chip.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("25_7_sub_chip"))
    assert "invoice_type=subscription" in financial_admin_page.url
    assert "tab=invoices" in financial_admin_page.url


@pytest.mark.asyncio
async def test_25_8_bkg_chip_filters_to_booking_invoices(financial_admin_page: Page):
    """Clicking the BKG chip adds invoice_type=booking to the URL."""
    await financial_admin_page.goto(INVOICES_TAB_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    bkg_chip = financial_admin_page.locator("a.btn", has_text="BKG").first
    await bkg_chip.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("25_8_bkg_chip"))
    assert "invoice_type=booking" in financial_admin_page.url
    assert "tab=invoices" in financial_admin_page.url


@pytest.mark.asyncio
async def test_25_9_all_chip_clears_invoice_type_filter(financial_admin_page: Page):
    """'All' chip removes invoice_type from URL while keeping tab=invoices."""
    await financial_admin_page.goto(f"{INVOICES_TAB_URL}&invoice_type=booking")
    await financial_admin_page.wait_for_load_state("networkidle")
    # Scope to filter chip links that point to the invoices tab (avoids nav "Mark all read" link)
    all_chip = financial_admin_page.locator("a.btn[href*='tab=invoices']", has_text="All").first
    await all_chip.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("25_9_all_chip"))
    assert "invoice_type" not in financial_admin_page.url
    assert "tab=invoices" in financial_admin_page.url
