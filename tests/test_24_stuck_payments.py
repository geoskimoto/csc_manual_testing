"""Section 24 — Stuck Payment Dashboard

Access is restricted to Financial Administrators only. Tests cover:
- Access control (anonymous, member, booking admin → 403; financial admin → 200)
- Page structure (stat cards, section headings, action links)
- Seeded data (unresolved record in unresolved table, resolved record in recently-resolved table)
"""
import pytest
from playwright.async_api import Page
from tests.helpers import STUCK_PAYMENTS_URL, screenshot_path

# Payment intent IDs created by seed_test_data step 9
UNRESOLVED_PI_ID = "pi_seed_test_unresolved"
RESOLVED_PI_ID = "pi_seed_test_resolved"


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_24_1_anonymous_gets_403(page: Page):
    """Unauthenticated request to the stuck payment dashboard returns 403."""
    response = await page.goto(STUCK_PAYMENTS_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("24_1_anonymous_403"))
    assert response.status == 403, f"Expected 403 for anonymous user, got {response.status}"


@pytest.mark.asyncio
async def test_24_2_member_gets_403(alice_page: Page):
    """Regular member cannot access the stuck payment dashboard (403)."""
    response = await alice_page.goto(STUCK_PAYMENTS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("24_2_member_403"))
    assert response.status == 403, f"Expected 403 for member, got {response.status}"


@pytest.mark.asyncio
async def test_24_3_booking_admin_gets_403(booking_admin_page: Page):
    """Booking Administrator cannot access the stuck payment dashboard (403)."""
    response = await booking_admin_page.goto(STUCK_PAYMENTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("24_3_booking_admin_403"))
    assert response.status == 403, f"Expected 403 for booking admin, got {response.status}"


@pytest.mark.asyncio
async def test_24_4_financial_admin_gets_200(financial_admin_page: Page):
    """Financial Administrator can access the stuck payment dashboard (200)."""
    response = await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("24_4_financial_admin_200"))
    assert response.status == 200, f"Expected 200 for financial admin, got {response.status}"
    content = await financial_admin_page.content()
    assert "stuck payment" in content.lower(), "Page title/content does not mention 'stuck payment'"


# ---------------------------------------------------------------------------
# Page structure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_24_5_dashboard_has_stat_cards(financial_admin_page: Page):
    """Dashboard shows exactly 5 stat cards."""
    await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    cards = financial_admin_page.locator(".dashboard-cards .card")
    count = await cards.count()
    await financial_admin_page.screenshot(path=screenshot_path("24_5_stat_cards"))
    assert count == 5, f"Expected 5 stat cards, found {count}"


@pytest.mark.asyncio
async def test_24_6_dashboard_has_section_headings(financial_admin_page: Page):
    """Dashboard shows all 4 required section headings."""
    await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("24_6_section_headings"))
    assert "Error Type Breakdown" in content, "Missing 'Error Type Breakdown' heading"
    assert "Resolution Actions" in content, "Missing 'Resolution Actions' heading"
    assert "Recent Unresolved Stuck Payments" in content, "Missing 'Recent Unresolved Stuck Payments' heading"
    assert "Recently Resolved" in content, "Missing 'Recently Resolved' heading"


@pytest.mark.asyncio
async def test_24_7_action_links_present(financial_admin_page: Page):
    """Dashboard includes action links to the Django admin stuck payment list."""
    await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("24_7_action_links"))
    assert "View All Stuck Payments" in content, "Missing 'View All Stuck Payments' link"
    assert "View Unresolved Only" in content, "Missing 'View Unresolved Only' link"


# ---------------------------------------------------------------------------
# Seeded data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_24_8_unresolved_record_visible(financial_admin_page: Page):
    """Seeded unresolved stuck payment appears in the Recent Unresolved table."""
    await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("24_8_unresolved_record"))
    assert UNRESOLVED_PI_ID in content, (
        f"Seeded unresolved payment intent '{UNRESOLVED_PI_ID}' not found — "
        "run 'python manage.py seed_test_data' on the deployed site"
    )


@pytest.mark.asyncio
async def test_24_9_resolved_record_visible(financial_admin_page: Page):
    """Seeded resolved stuck payment appears in the Recently Resolved section."""
    await financial_admin_page.goto(STUCK_PAYMENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("24_9_resolved_record"))
    assert RESOLVED_PI_ID in content, (
        f"Seeded resolved payment intent '{RESOLVED_PI_ID}' not found — "
        "run 'python manage.py seed_test_data' on the deployed site"
    )
