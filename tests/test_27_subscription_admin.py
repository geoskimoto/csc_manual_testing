"""Section 27 — Subscription Admin: List, Statistics, Details, and Assign

Accessible to both Booking Admins and Financial Admins.
Tests cover access control, list content for seeded members, statistics cards,
the subscription details modal, and the assign membership page.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import (
    SUBS_ADMIN_URL, SUBS_ADMIN_ASSIGN_URL, LOGIN_URL, screenshot_path
)


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_27_1_list_loads_for_financial_admin(financial_admin_page: Page):
    """Subscription admin list loads for Financial Admin (200)."""
    response = await financial_admin_page.goto(SUBS_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("27_1_fa_subs_list"))
    assert response.status == 200
    content = await financial_admin_page.content()
    assert "Membership" in content


@pytest.mark.asyncio
async def test_27_2_list_loads_for_booking_admin(booking_admin_page: Page):
    """Subscription admin list loads for Booking Admin (200)."""
    response = await booking_admin_page.goto(SUBS_ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("27_2_ba_subs_list"))
    assert response.status == 200


@pytest.mark.asyncio
async def test_27_3_member_cannot_access(alice_page: Page):
    """Regular member is redirected away from subscription admin list."""
    await alice_page.goto(SUBS_ADMIN_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("27_3_member_blocked"))
    assert SUBS_ADMIN_URL.split("3rdplaces.io")[1] not in alice_page.url \
        or "/sign-in" in alice_page.url or "/dashboard" in alice_page.url


# ---------------------------------------------------------------------------
# List content
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_27_4_list_shows_alice_subscription(financial_admin_page: Page):
    """Seeded Alice subscription appears in the admin list."""
    await financial_admin_page.goto(SUBS_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("27_4_alice_in_list"))
    assert "alice" in content.lower() or "tester" in content.lower(), \
        "Alice's subscription not found in the list"


@pytest.mark.asyncio
async def test_27_5_list_shows_status_badges(financial_admin_page: Page):
    """Subscription list rows contain status badges (Active, Pending, etc.)."""
    await financial_admin_page.goto(SUBS_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("27_5_status_badges"))
    assert "Active" in content or "Pending" in content or "Canceled" in content, \
        "No status badges visible in subscription list"


@pytest.mark.asyncio
async def test_27_6_statistics_cards_present(financial_admin_page: Page):
    """Dashboard statistics cards are present (Active, Expiring, Revenue)."""
    await financial_admin_page.goto(SUBS_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("27_6_stats_cards"))
    assert "Active" in content
    # Revenue stats show dollar amounts
    assert "$" in content


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_27_7_view_details_modal_opens(financial_admin_page: Page):
    """Clicking View Details on a subscription opens the details modal."""
    await financial_admin_page.goto(SUBS_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    # Click the first View Details button
    details_btn = financial_admin_page.locator(".view-details-btn").first
    count = await details_btn.count()
    if count == 0:
        pytest.skip("No subscription rows found — seed data may be missing")
    await details_btn.click()
    # Wait for modal to appear (AJAX call)
    await financial_admin_page.wait_for_selector("#subscriptionDetailsModal.show", timeout=5000)
    await financial_admin_page.screenshot(path=screenshot_path("27_7_details_modal"))
    content = await financial_admin_page.content()
    assert "Membership" in content or "Profile" in content


@pytest.mark.asyncio
async def test_27_8_assign_membership_page_loads(financial_admin_page: Page):
    """Assign Membership page loads with a member search/select field."""
    response = await financial_admin_page.goto(SUBS_ADMIN_ASSIGN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("27_8_assign_membership"))
    assert response.status == 200
    content = await financial_admin_page.content()
    assert "Assign" in content or "Membership" in content
    # Page should have a member search or select field
    assert "profile" in content.lower() or "member" in content.lower() or "search" in content.lower()
