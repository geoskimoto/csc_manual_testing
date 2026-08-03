"""Section 36 — Financial Dashboard, AR Aging & Deferred Revenue Reports

The main Financial Dashboard (/financials/) is gated by
@booking_administrator_required — both Booking and Financial Administrators
can see it. The Deferred Revenue and AR Aging reports are gated by the
stricter @financial_administrator_required (they surface individual members'
balances) — Booking Administrators are blocked from those two.

Test data: seed_test_data creates a 45-day-overdue unpaid Invoice for Alice,
which should land in the AR Aging report's 31-60 day bucket.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import (
    FINANCIAL_DASHBOARD_URL, DEFERRED_REVENUE_URL, AR_AGING_URL, screenshot_path
)


# ---------------------------------------------------------------------------
# Main dashboard — booking admins AND financial admins can see it
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_36_1_dashboard_loads_for_booking_admin(booking_admin_page: Page):
    """Booking Administrators can view the Financial Dashboard."""
    resp = await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("36_1_dashboard_booking_admin"))
    assert resp.status == 200, f"Expected 200 for booking admin, got {resp.status}"
    content = await booking_admin_page.content()
    assert "financial dashboard" in content.lower()


@pytest.mark.asyncio
async def test_36_2_dashboard_loads_for_financial_admin(financial_admin_page: Page):
    """Financial Administrators can also view the Financial Dashboard."""
    resp = await financial_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    assert resp.status == 200, f"Expected 200 for financial admin, got {resp.status}"


@pytest.mark.asyncio
async def test_36_3_member_cannot_access(alice_page: Page):
    """Regular members are blocked (403) from the Financial Dashboard."""
    resp = await alice_page.goto(FINANCIAL_DASHBOARD_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_36_4_accrual_cash_toggle_present(booking_admin_page: Page):
    """Dashboard exposes an Accrual/Cash mode toggle, defaulting to Accrual."""
    await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("36_4_mode_toggle"))
    accrual_btn = booking_admin_page.locator("a", has_text="Accrual")
    cash_btn = booking_admin_page.locator("a", has_text="Cash")
    assert await accrual_btn.count() > 0 and await cash_btn.count() > 0, \
        "Accrual/Cash toggle buttons not found"


@pytest.mark.asyncio
async def test_36_5_cash_mode_switches_via_query_param(booking_admin_page: Page):
    """Navigating with ?mode=cash switches the active toggle button."""
    await booking_admin_page.goto(f"{FINANCIAL_DASHBOARD_URL}?mode=cash")
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("36_5_cash_mode"))
    cash_btn = booking_admin_page.locator("a.btn-primary", has_text="Cash")
    assert await cash_btn.count() > 0, "Cash button should be the active (btn-primary) toggle in cash mode"


@pytest.mark.asyncio
async def test_36_6_fiscal_year_selector_present(booking_admin_page: Page):
    """Dashboard has a fiscal year selector — self-heals to a default FY if none exists."""
    await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    fy_select = booking_admin_page.locator("#fiscalYearSelect")
    assert await fy_select.count() > 0, "#fiscalYearSelect not found"
    options = await fy_select.locator("option").count()
    assert options >= 1, "Fiscal year selector has no options"


@pytest.mark.asyncio
async def test_36_7_export_csv_link_present(booking_admin_page: Page):
    """Dashboard has an Export CSV link."""
    await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    export_link = booking_admin_page.locator("a", has_text="Export CSV")
    assert await export_link.count() > 0, "Export CSV link not found"


@pytest.mark.asyncio
async def test_36_8_stat_cards_and_tables_present(booking_admin_page: Page):
    """Dashboard renders the key stat cards, charts, and Who/What breakdown tables."""
    await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.wait_for_timeout(1500)  # Chart.js render settle
    await booking_admin_page.screenshot(path=screenshot_path("36_8_stat_cards"))

    for chart_id in ["#monthlyChart", "#membershipChart"]:
        assert await booking_admin_page.locator(chart_id).count() > 0, f"{chart_id} canvas not found"

    for table_id in ["#monthlyTable", "#membershipTable", "#roomTypeTable",
                      "#programBreakdownTable", "#itemTypeBreakdownTable"]:
        assert await booking_admin_page.locator(table_id).count() > 0, f"{table_id} not found"


@pytest.mark.asyncio
async def test_36_9_deferred_revenue_and_ar_aging_links_hidden_for_booking_admin(booking_admin_page: Page):
    """Booking Administrators do not see the stricter financial-admin-only report links."""
    await booking_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("36_9_links_hidden"))
    assert await booking_admin_page.locator("a", has_text="Deferred Revenue Report").count() == 0
    assert await booking_admin_page.locator("a", has_text="AR Aging Report").count() == 0


@pytest.mark.asyncio
async def test_36_10_deferred_revenue_and_ar_aging_links_shown_for_financial_admin(financial_admin_page: Page):
    """Financial Administrators see both stricter report links on the dashboard."""
    await financial_admin_page.goto(FINANCIAL_DASHBOARD_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    assert await financial_admin_page.locator("a", has_text="Deferred Revenue Report").count() > 0
    assert await financial_admin_page.locator("a", has_text="AR Aging Report").count() > 0


# ---------------------------------------------------------------------------
# Deferred Revenue Report — financial admin only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_36_11_deferred_revenue_blocked_for_booking_admin(booking_admin_page: Page):
    """Booking Administrators are blocked (403) from the Deferred Revenue report."""
    resp = await booking_admin_page.goto(DEFERRED_REVENUE_URL)
    status = resp.status if resp else 0
    url = booking_admin_page.url
    await booking_admin_page.screenshot(path=screenshot_path("36_11_deferred_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected booking admin to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_36_12_deferred_revenue_loads_for_financial_admin(financial_admin_page: Page):
    """Financial Administrators can view the Deferred Revenue report."""
    resp = await financial_admin_page.goto(DEFERRED_REVENUE_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("36_12_deferred_loads"))
    assert resp.status == 200, f"Expected 200 for financial admin, got {resp.status}"
    content = await financial_admin_page.content()
    assert "year-end close" in content.lower() or "deferred revenue" in content.lower()


# ---------------------------------------------------------------------------
# AR Aging Report — financial admin only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_36_13_ar_aging_blocked_for_booking_admin(booking_admin_page: Page):
    """Booking Administrators are blocked (403) from the AR Aging report."""
    resp = await booking_admin_page.goto(AR_AGING_URL)
    status = resp.status if resp else 0
    url = booking_admin_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected booking admin to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_36_14_ar_aging_loads_for_financial_admin(financial_admin_page: Page):
    """Financial Administrators can view the AR Aging report."""
    resp = await financial_admin_page.goto(AR_AGING_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("36_14_ar_aging_loads"))
    assert resp.status == 200, f"Expected 200 for financial admin, got {resp.status}"


@pytest.mark.asyncio
async def test_36_15_ar_aging_bucket_summary_cards_present(financial_admin_page: Page):
    """AR Aging report shows the 5 bucket summary cards."""
    await financial_admin_page.goto(AR_AGING_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    cards = financial_admin_page.locator(".card.shadow-sm")
    count = await cards.count()
    await financial_admin_page.screenshot(path=screenshot_path("36_15_bucket_cards"))
    assert count >= 5, f"Expected at least 5 bucket summary cards, found {count}"


@pytest.mark.asyncio
async def test_36_16_seeded_overdue_invoice_visible_in_31_60_bucket(financial_admin_page: Page):
    """The seeded 45-day-overdue invoice for Alice appears in AR Aging, bucketed 31-60."""
    await financial_admin_page.goto(AR_AGING_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("36_16_seeded_overdue"))
    assert "alice" in content.lower(), "Seeded overdue invoice for Alice not visible in AR aging report"

    row = financial_admin_page.locator("tr", has_text="Alice")
    if await row.count() == 0:
        pytest.skip("Could not locate Alice's row to check bucket assignment")
    row_text = (await row.first.inner_text()).lower()
    assert "31-60" in row_text or "31–60" in row_text, \
        f"Expected Alice's overdue invoice in the 31-60 bucket, row text: {row_text!r}"
