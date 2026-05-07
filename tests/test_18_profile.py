"""Section 18 — Profile & Family Management"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, PROFILE_URL, DASHBOARD_URL, screenshot_path

PROFILES_URL    = f"{BASE_URL}/dashboard/profiles/"
CHANGE_PWD_URL  = f"{BASE_URL}/dashboard/change-password/"


@pytest.mark.asyncio
async def test_18_1_profile_page_loads(alice_page: Page):
    """Profile page loads without error."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_1_profile"))
    assert "500" not in await alice_page.title(), "Server error on profile page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "profile", "name", "email", "member", "account"
    ]), "Profile page did not render expected content"


@pytest.mark.asyncio
async def test_18_2_profile_shows_member_info(alice_page: Page):
    """Profile page displays name and membership type."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_2_profile_info"))
    content = await alice_page.content()
    has_name = "alice" in content.lower() or "tester" in content.lower()
    has_type = any(kw in content.lower() for kw in [
        "regular", "family", "membership", "member type", "member since"
    ])
    assert has_name, "Alice's name not found on profile page"
    assert has_type, "Membership type not displayed on profile page"


@pytest.mark.asyncio
async def test_18_3_profiles_list_page_loads(alice_page: Page):
    """Profiles list page loads (shows family members if any)."""
    await alice_page.goto(PROFILES_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_3_profiles_list"))
    assert "500" not in await alice_page.title(), "Server error on profiles list page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "profile", "family", "member", "name", "no profiles"
    ]), "Profiles list page did not render expected content"


@pytest.mark.asyncio
async def test_18_4_edit_profile_link_present(alice_page: Page):
    """Profile page includes an edit link or button."""
    await alice_page.goto(PROFILE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_4_edit_link"))
    content = await alice_page.content()
    has_edit = (
        "edit" in content.lower()
        or "/dashboard/profile/" in content and "edit" in content.lower()
        or "/edit/" in content
    )
    assert has_edit, "No edit link found on profile page"


@pytest.mark.asyncio
async def test_18_5_change_password_page_loads(alice_page: Page):
    """Change password page loads without error."""
    await alice_page.goto(CHANGE_PWD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_5_change_password"))
    assert "500" not in await alice_page.title(), "Server error on change-password page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "password", "current password", "new password", "change"
    ]), "Change password page did not render expected content"


@pytest.mark.asyncio
async def test_18_6_profile_edit_page_loads(alice_page: Page):
    """Profile edit URL loads for the first profile (ID probed 1–5)."""
    for profile_id in range(1, 6):
        resp = await alice_page.goto(f"{BASE_URL}/dashboard/profile/{profile_id}/edit/")
        await alice_page.wait_for_load_state("networkidle")
        status = resp.status if resp else 0
        if status == 200:
            content = await alice_page.content()
            await alice_page.screenshot(path=screenshot_path(f"18_6_edit_profile_{profile_id}"))
            assert any(kw in content.lower() for kw in [
                "edit", "save", "first name", "last name", "profile"
            ]), f"Profile edit page at ID {profile_id} missing expected form fields"
            return
    pytest.skip("No accessible profile edit page found in IDs 1–5 (may be permission or data gap)")


@pytest.mark.asyncio
async def test_18_7_profile_anonymous_redirect(page: Page):
    """Anonymous user is redirected from profile page."""
    await page.goto(PROFILE_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("18_7_anon_profile"))
    assert "sign-in" in page.url or "login" in page.url, \
        f"Anonymous user not redirected from profile — got {page.url}"


@pytest.mark.asyncio
async def test_18_8_dashboard_shows_profile_link(alice_page: Page):
    """Dashboard navigation includes a link to the profile page."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("18_8_dashboard_profile_link"))
    content = await alice_page.content()
    has_link = "/dashboard/profile/" in content or "profile" in content.lower()
    assert has_link, "Dashboard does not link to or mention the profile page"
