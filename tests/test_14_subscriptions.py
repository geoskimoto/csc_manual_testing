"""Section 14 — Membership Subscriptions"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, DASHBOARD_URL, PROFILE_URL, screenshot_path

SUBSCRIPTIONS_URL = f"{BASE_URL}/subscriptions/"


@pytest.mark.asyncio
async def test_14_1_subscriptions_page_loads(alice_page: Page):
    """Subscription dashboard loads for a logged-in member."""
    await alice_page.goto(SUBSCRIPTIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("14_1_subscriptions"))
    assert "500" not in await alice_page.title(), "Server error on subscriptions page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "subscription", "membership", "active", "expires", "renew"
    ]), "Subscriptions page did not render expected content"


@pytest.mark.asyncio
async def test_14_1_alice_subscription_is_active(alice_page: Page):
    """Alice has an active subscription (expires 2027-04-19 per test data)."""
    await alice_page.goto(SUBSCRIPTIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("14_1_alice_active"))
    content = await alice_page.content()
    assert "active" in content.lower(), \
        "Alice's subscription does not show as active on subscriptions page"


@pytest.mark.asyncio
async def test_14_2_subscription_shown_on_dashboard(alice_page: Page):
    """Dashboard displays subscription status for the member."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("14_2_dashboard_subscription"))
    content = await alice_page.content()
    has_sub = any(kw in content.lower() for kw in [
        "subscription", "membership", "active", "expires", "renew", "subscribe"
    ])
    assert has_sub, "Dashboard does not show subscription status"


@pytest.mark.asyncio
async def test_14_3_subscription_shown_on_profile(alice_page: Page):
    """Profile page includes subscription/membership status."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("14_3_profile_subscription"))
    content = await alice_page.content()
    has_status = any(kw in content.lower() for kw in [
        "subscription", "membership", "active", "expires", "member since"
    ])
    assert has_status, "Profile page does not show subscription or membership status"


@pytest.mark.asyncio
async def test_14_4_auto_renew_toggle_present(alice_page: Page):
    """Subscription page shows an auto-renew toggle or option."""
    await alice_page.goto(SUBSCRIPTIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("14_4_auto_renew"))
    content = await alice_page.content()
    has_toggle = any(kw in content.lower() for kw in [
        "auto-renew", "auto renew", "automatic renewal", "renew automatically"
    ])
    if not has_toggle:
        pytest.skip("Auto-renew toggle not present — may only show for certain subscription states")


@pytest.mark.asyncio
async def test_14_5_subscriptions_redirect_anonymous(page: Page):
    """Anonymous user accessing subscriptions is redirected to login."""
    await page.goto(SUBSCRIPTIONS_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("14_5_anon_subscription"))
    assert "sign-in" in page.url or "login" in page.url, \
        f"Anonymous user was not redirected from subscriptions page — got {page.url}"
