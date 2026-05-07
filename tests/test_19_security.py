"""Section 19 — Security & Access Control"""
import pytest
import urllib.request
import urllib.error
from playwright.async_api import Page
from tests.helpers import BASE_URL, LOGIN_URL, ADD_TO_CART_URL, ADMIN_URL, screenshot_path, BOB

# Only /dashboard/ is confirmed auth-gated; availability and cart are public (browse-only)
PROTECTED_URLS = [
    "/dashboard/",
    "/dashboard/wallet/",
    "/dashboard/profile/",
]

# Real admin URL from URL_REFERENCE.md
ADMIN_PATHS = [
    "/admin-bookings/",
    "/admin-bookings/manage-bookings/",
    "/billing/admin-tool/",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PROTECTED_URLS)
async def test_19_1_anonymous_redirects_to_login(page: Page, path: str):
    """Anonymous user is redirected to sign-in for auth-gated pages."""
    await page.goto(f"{BASE_URL}{path}")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path(f"19_1_anon_{path.strip('/').replace('/', '_')}"))
    assert "sign-in" in page.url or "login" in page.url, \
        f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ADMIN_PATHS)
async def test_19_2_member_cannot_access_admin(alice_page: Page, path: str):
    """Regular member is blocked from admin URLs (403, 404, or redirect)."""
    resp = await alice_page.goto(f"{BASE_URL}{path}")
    await alice_page.wait_for_load_state("networkidle")
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path(f"19_2_{path.strip('/').replace('/', '_')}"))
    is_blocked = status in (403, 404) or "sign-in" in url or "login" in url
    assert is_blocked, f"Member reached admin page {path} — status {status}, url {url}"


@pytest.mark.asyncio
async def test_19_3_cannot_access_other_users_booking(alice_page: Page):
    """Alice cannot view another user's booking detail by guessing IDs."""
    for booking_id in range(1, 21):
        resp = await alice_page.goto(f"{BASE_URL}/dashboard/booking_detail/{booking_id}/")
        await alice_page.wait_for_load_state("networkidle")
        status = resp.status if resp else 0
        if status == 200:
            content = await alice_page.content()
            assert BOB["email"].split("@")[0] not in content.lower(), \
                f"Alice can see Bob's data at booking_detail/{booking_id}/"
    await alice_page.screenshot(path=screenshot_path("19_3_cross_user"))


@pytest.mark.asyncio
async def test_19_5_csrf_protection(page: Page):
    """POST to add-to-cart without CSRF token is rejected (403)."""
    try:
        req = urllib.request.Request(
            ADD_TO_CART_URL,
            data=b"check_in_date=2026-06-01&check_out_date=2026-06-03",
            method="POST",
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    await page.screenshot(path=screenshot_path("19_5_csrf"))
    assert status == 403, f"Expected 403 for missing CSRF token, got {status}"
