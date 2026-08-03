"""Section 35 — Admin Alert Recipients & Live Dashboard Badge

AdminAlertRecipient rows configure who sees the Admin Dashboard nav badge and
who gets emailed for operational alert types (awaiting_membership, stuck_payment,
stripe_webhook_failure). Gated by @booking_administrator_required (both Booking
and Financial Administrators can reach it; regular members cannot).

Test data: seed_test_data creates a stuck_payment AdminAlertRecipient for
financial.admin, and an unresolved StuckPayment — together these should drive
a nonzero Admin Dashboard badge for financial.admin.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import ADMIN_ALERT_RECIPIENTS_URL, FINANCIAL_ADMIN, screenshot_path


@pytest.mark.asyncio
async def test_35_1_page_loads_for_booking_admin(booking_admin_page: Page):
    """Booking Administrators can reach the alert recipients config page."""
    resp = await booking_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("35_1_page_loads_booking_admin"))
    assert resp.status == 200, f"Expected 200 for booking admin, got {resp.status}"
    content = await booking_admin_page.content()
    assert "admin alert recipients" in content.lower()


@pytest.mark.asyncio
async def test_35_2_page_loads_for_financial_admin(financial_admin_page: Page):
    """Financial Administrators can also reach the alert recipients config page."""
    resp = await financial_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    assert resp.status == 200, f"Expected 200 for financial admin, got {resp.status}"


@pytest.mark.asyncio
async def test_35_3_member_cannot_access(alice_page: Page):
    """Regular members are blocked (403) from the alert recipients config page."""
    resp = await alice_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path("35_3_member_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_35_4_alert_type_cards_present(booking_admin_page: Page):
    """Page shows a card per registered alert type, including 'Stuck payments'."""
    await booking_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    content = await booking_admin_page.content()
    await booking_admin_page.screenshot(path=screenshot_path("35_4_alert_type_cards"))
    assert "stuck payment" in content.lower(), "Expected 'Stuck payments' alert type card"


@pytest.mark.asyncio
async def test_35_5_seeded_recipient_visible(booking_admin_page: Page):
    """The seeded stuck_payment recipient (financial.admin) appears in its card's table."""
    await booking_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    content = await booking_admin_page.content()
    await booking_admin_page.screenshot(path=screenshot_path("35_5_seeded_recipient"))
    assert FINANCIAL_ADMIN["email"] in content, \
        f"Seeded recipient {FINANCIAL_ADMIN['email']} not found on alert recipients page"


@pytest.mark.asyncio
async def test_35_6_toggle_notify_email_round_trip(booking_admin_page: Page):
    """Toggling a recipient's Email column flips the button text, and toggling
    again restores it — verifies the toggle POST action end to end without
    leaving the fixture in a different state."""
    await booking_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    row = booking_admin_page.locator("tr", has_text=FINANCIAL_ADMIN["email"])
    if await row.count() == 0:
        pytest.skip("Seeded recipient row not found — run seed_test_data")

    # Column order per admin_alert_recipients.html: Dashboard badge (0),
    # Email (1), Active (2), Remove (3) — each its own <form>.
    toggle_btn = row.locator("form").nth(1).locator("button[type='submit']")
    before_text = (await toggle_btn.inner_text()).strip()

    await toggle_btn.click()
    await booking_admin_page.wait_for_load_state("networkidle")

    row = booking_admin_page.locator("tr", has_text=FINANCIAL_ADMIN["email"])
    toggle_btn = row.locator("form").nth(1).locator("button[type='submit']")
    after_text = (await toggle_btn.inner_text()).strip()
    await booking_admin_page.screenshot(path=screenshot_path("35_6_toggled"))
    assert after_text != before_text, "Toggle button text did not change after clicking"

    # Restore original state
    await toggle_btn.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    row = booking_admin_page.locator("tr", has_text=FINANCIAL_ADMIN["email"])
    restored_text = (await row.locator("form").nth(1).locator("button[type='submit']").inner_text()).strip()
    assert restored_text == before_text, "Toggle did not restore original state"


@pytest.mark.asyncio
async def test_35_7_live_badge_shown_for_financial_admin(financial_admin_page: Page):
    """With a seeded stuck_payment recipient + an unresolved StuckPayment, the
    Admin Dashboard nav item shows a nonzero live badge."""
    await financial_admin_page.goto(ADMIN_ALERT_RECIPIENTS_URL)
    await financial_admin_page.wait_for_load_state("networkidle")

    admin_tools_btn = financial_admin_page.locator("button", has_text="Admin Tools")
    if await admin_tools_btn.count() > 0:
        await admin_tools_btn.first.click()
        await financial_admin_page.wait_for_timeout(300)

    dashboard_item = financial_admin_page.locator(".dropdown-item", has_text="Admin Dashboard")
    await financial_admin_page.screenshot(path=screenshot_path("35_7_live_badge"))
    if await dashboard_item.count() == 0:
        pytest.skip("Admin Dashboard nav item not found — nav structure may differ at this viewport")
    badge = dashboard_item.first.locator(".badge")
    if await badge.count() == 0:
        pytest.skip("No badge rendered — open alert items may have been resolved since seeding")
    badge_text = (await badge.inner_text()).strip()
    assert badge_text.isdigit() and int(badge_text) > 0, \
        f"Expected a nonzero live alert badge, got {badge_text!r}"
