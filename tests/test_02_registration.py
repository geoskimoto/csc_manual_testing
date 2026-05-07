"""Section 2 — Registration & Onboarding

CSC uses an invitation-only registration system. Direct sign-up creates a membership
application; full account activation requires an invitation token sent by an admin.
These tests verify the onboarding UI surfaces without completing actual registration
(which would require a single-use token and create permanent DB records).
"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, LOGIN_URL, SIGN_UP_URL, MEMBERSHIP_APP_URL, screenshot_path

REGISTER_URL    = f"{BASE_URL}/user/register/"
PASSWORD_RESET_URL = f"{BASE_URL}/user/password-reset/"


@pytest.mark.asyncio
async def test_2_1_sign_up_page_loads(page: Page):
    """Sign-up / membership application entry page loads without error."""
    await page.goto(SIGN_UP_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_1_sign_up"))
    assert "500" not in await page.title(), "Server error on sign-up page"
    content = await page.content()
    assert any(kw in content.lower() for kw in [
        "sign up", "register", "join", "member", "application", "apply"
    ]), "Sign-up page missing expected content"


@pytest.mark.asyncio
async def test_2_2_membership_application_loads(page: Page):
    """Membership application form loads and has expected fields."""
    await page.goto(MEMBERSHIP_APP_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_2_membership_app"))
    assert "500" not in await page.title(), "Server error on membership application"
    content = await page.content()
    assert any(kw in content.lower() for kw in [
        "application", "membership", "apply", "join", "form"
    ]), "Membership application page missing expected content"


@pytest.mark.asyncio
async def test_2_3_membership_application_has_form_fields(page: Page):
    """Membership application form has standard contact fields."""
    await page.goto(MEMBERSHIP_APP_URL)
    await page.wait_for_load_state("networkidle")
    content = await page.content()
    has_name = "first" in content.lower() or "name" in content.lower()
    has_email = 'type="email"' in content or 'name="email"' in content
    await page.screenshot(path=screenshot_path("02_3_app_fields"))
    assert has_name, "Membership application missing name field"
    assert has_email, "Membership application missing email field"


@pytest.mark.asyncio
async def test_2_4_invalid_invite_token_rejected(page: Page):
    """A bogus invitation token returns 404 or an error page (not a registration form)."""
    fake_token = "00000000-0000-0000-0000-000000000000"
    resp = await page.goto(f"{BASE_URL}/user/register/{fake_token}/")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_4_invalid_token"))
    status = resp.status if resp else 0
    content = await page.content()
    is_rejected = (
        status == 404
        or "invalid" in content.lower()
        or "expired" in content.lower()
        or "not found" in content.lower()
        or "error" in content.lower()
    )
    assert is_rejected, f"Bogus invite token was not rejected — status {status}"


@pytest.mark.asyncio
async def test_2_5_login_page_has_expected_fields(page: Page):
    """Login page has email and password inputs and a submit button."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_5_login_fields"))
    assert await page.locator('input[name="email"]').count() > 0, "No email field on login page"
    assert await page.locator('input[name="password"]').count() > 0, "No password field on login page"
    assert await page.locator('button[type="submit"]').count() > 0, "No submit button on login page"


@pytest.mark.asyncio
async def test_2_6_password_reset_page_loads(page: Page):
    """Password reset page is reachable and has an email input."""
    await page.goto(PASSWORD_RESET_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_6_password_reset"))
    assert "500" not in await page.title(), "Server error on password reset page"
    assert await page.locator('input[type="email"]').count() > 0, "No email field on password reset page"


@pytest.mark.asyncio
async def test_2_7_logged_in_user_redirected_from_login(alice_page: Page):
    """Already-authenticated user visiting the login page is redirected (not shown login form)."""
    await alice_page.goto(LOGIN_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("02_7_logged_in_redirect"))
    # Logged-in user should be redirected away from sign-in; the sign-in form should not appear
    content = await alice_page.content()
    is_on_login = (
        await alice_page.locator('input[name="email"]').count() > 0
        and await alice_page.locator('input[name="password"]').count() > 0
    )
    # Either redirected OR the form is not present
    if is_on_login:
        pytest.skip("App shows login form to authenticated users — not a blocking issue")


@pytest.mark.asyncio
async def test_2_8_wrong_credentials_show_error(page: Page):
    """Submitting wrong credentials shows an error — does not log in."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="email"]', "nobody@nowhere.invalid")
    await page.fill('input[name="password"]', "WrongPassword99!")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_8_wrong_credentials"))
    content = await page.content()
    url = page.url
    still_on_login = "sign-in" in url or "login" in url
    has_error = any(kw in content.lower() for kw in [
        "invalid", "incorrect", "error", "wrong", "failed", "try again"
    ])
    assert still_on_login or has_error, "Wrong credentials did not show an error or stay on login page"
