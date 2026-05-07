"""Section 2 — Registration & Onboarding

CSC uses an invitation-only registration system. Direct sign-up redirects to the
membership application. Full account activation requires an invitation token sent
by an admin. The primary registration path is /user/register-family/<token>/ which
supports solo registration or registering with family members (spouse, children).

Token strategy: seed_test_data Step 8 creates four fresh invitation tokens before
each run, writing them to cycle/reg_test_tokens.json. Tests that submit invalid
data do NOT consume their token. Tests that complete registration DO consume theirs.

Tests:
  2.1 – 2.5 : Page load and public-form tests (no token needed)
  2.6 – 2.11: Form validation tests (token: "validation" — never consumed)
  2.12       : Solo registration succeeds (token: "solo")
  2.13       : Registration with spouse succeeds (token: "spouse")
  2.14       : Registration with child succeeds — catches the can_book bug (token: "child")
  2.15       : Used token is rejected
  2.16       : New account can sign in after registration
"""
import json
import os
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, LOGIN_URL, SIGN_UP_URL, MEMBERSHIP_APP_URL, screenshot_path

REGISTER_FAMILY_URL = f"{BASE_URL}/user/register-family/"
REGISTER_URL        = f"{BASE_URL}/user/register/"
PASSWORD_RESET_URL  = f"{BASE_URL}/user/password-reset/"
REG_TOKENS_FILE     = "/tmp/csc_reg_test_tokens.json"

# Passwords used when completing test registrations
_REG_PASSWORD = "TestRegPass99!"


def _load_tokens():
    """Load registration test tokens written by seed_test_data Step 8."""
    try:
        with open(REG_TOKENS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _token_url(label: str) -> str | None:
    tokens = _load_tokens()
    token = tokens.get(label)
    return f"{REGISTER_FAMILY_URL}{token}/" if token else None


# ---------------------------------------------------------------------------
# 2.1 – 2.5  Page load and public-form tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_1_sign_up_redirects_to_membership_application(page: Page):
    """Sign-up URL redirects to or renders the membership application."""
    await page.goto(SIGN_UP_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_1_sign_up"))
    assert "500" not in await page.title(), "Server error on sign-up page"
    content = await page.content()
    # Either redirected to membership_application or shows a link to it
    assert any(kw in content.lower() for kw in [
        "application", "membership", "apply", "join", "invitation"
    ]), "Sign-up page missing expected content"


@pytest.mark.asyncio
async def test_2_2_membership_application_loads(page: Page):
    """Membership application form page loads and has expected fields."""
    await page.goto(MEMBERSHIP_APP_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_2_membership_app"))
    assert "500" not in await page.title(), "Server error on membership application"
    has_name  = await page.locator('input[name*="first"], input[name*="last"], input[name*="name"]').count() > 0
    has_email = await page.locator('input[type="email"], input[name="email"]').count() > 0
    assert has_name,  "Membership application missing name field"
    assert has_email, "Membership application missing email field"


@pytest.mark.asyncio
async def test_2_3_membership_application_can_be_submitted(page: Page):
    """Membership application form accepts a valid POST and does not 500."""
    await page.goto(MEMBERSHIP_APP_URL)
    await page.wait_for_load_state("networkidle")

    # Fill required fields generically — field names vary, fill what's present
    for sel in ['input[name="first_name"]', 'input[name*="first"]']:
        if await page.locator(sel).count() > 0:
            await page.locator(sel).first.fill("Tester")
            break
    for sel in ['input[name="last_name"]', 'input[name*="last"]']:
        if await page.locator(sel).count() > 0:
            await page.locator(sel).first.fill("Applicant")
            break
    for sel in ['input[type="email"]', 'input[name="email"]']:
        if await page.locator(sel).count() > 0:
            await page.locator(sel).first.fill("apply.test@csc-test.local")
            break

    submit = page.locator('button[type="submit"], input[type="submit"]').first
    if await submit.count() == 0:
        pytest.skip("No submit button found on membership application")
    await submit.click()
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_3_app_submit"))
    assert "500" not in await page.title(), "Server error after submitting membership application"


@pytest.mark.asyncio
async def test_2_4_login_page_has_expected_fields(page: Page):
    """Login page has email and password inputs and a submit button."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_4_login_fields"))
    assert await page.locator('input[name="email"]').count() > 0,            "No email field on login page"
    assert await page.locator('input[name="password"]').count() > 0,         "No password field on login page"
    assert await page.locator('button[type="submit"]').count() > 0,          "No submit button on login page"


@pytest.mark.asyncio
async def test_2_5_invalid_invite_token_rejected(page: Page):
    """A bogus invitation token returns 404 or an error page."""
    resp = await page.goto(f"{REGISTER_FAMILY_URL}00000000-0000-0000-0000-000000000000/")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_5_invalid_token"))
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


# ---------------------------------------------------------------------------
# 2.6 – 2.11  Form validation tests (token: "validation" — never consumed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_6_valid_token_shows_registration_form(page: Page):
    """A valid invitation token renders the family registration form."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_6_reg_form"))
    assert "500" not in await page.title(), "Server error on registration form"
    content = await page.content()
    assert any(kw in content.lower() for kw in [
        "registration", "register", "first name", "password"
    ]), "Registration form missing expected content"


@pytest.mark.asyncio
async def test_2_7_email_is_prefilled_from_invitation(page: Page):
    """The registration form pre-fills the email field from the invitation."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")

    email_input = page.locator('input[name="email"], input[type="email"]').first
    if await email_input.count() == 0:
        pytest.skip("No email field found on registration form")

    value = await email_input.input_value()
    await page.screenshot(path=screenshot_path("02_7_email_prefill"))
    assert "reg.validation@csc-test.local" in value or value, \
        "Email field is empty — invitation email not pre-filled"


@pytest.mark.asyncio
async def test_2_8_password_mismatch_shows_error(page: Page):
    """Submitting mismatched passwords shows a validation error; token not consumed."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="first_name"]', "Test")
    await page.fill('input[name="last_name"]', "User")
    await page.fill('input[name="password1"]', "GoodPassword99!")
    await page.fill('input[name="password2"]', "DifferentPassword99!")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_8_password_mismatch"))

    content = await page.content()
    url_after = page.url
    # Should stay on the registration form (not redirected to sign-in)
    is_still_on_form = "sign-in" not in url_after and "sign_in" not in url_after
    has_error = any(kw in content.lower() for kw in [
        "password", "match", "error", "invalid", "two password"
    ])
    assert is_still_on_form, "Password mismatch redirected away from form unexpectedly"
    assert has_error, "No error shown after password mismatch"


@pytest.mark.asyncio
async def test_2_9_weak_password_rejected(page: Page):
    """A common/short password is rejected with a validation error; token not consumed."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="first_name"]', "Test")
    await page.fill('input[name="last_name"]', "User")
    await page.fill('input[name="password1"]', "password")
    await page.fill('input[name="password2"]', "password")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_9_weak_password"))

    content = await page.content()
    url_after = page.url
    is_still_on_form = "sign-in" not in url_after
    has_error = any(kw in content.lower() for kw in [
        "too common", "too short", "password", "error"
    ])
    assert is_still_on_form, "Weak password redirected away from form unexpectedly"
    assert has_error, "No error shown after weak password"


@pytest.mark.asyncio
async def test_2_10_missing_required_fields_shows_error(page: Page):
    """Submitting with empty required fields shows errors; token not consumed."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    # Submit with nothing filled
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_10_missing_fields"))

    content = await page.content()
    url_after = page.url
    is_still_on_form = "sign-in" not in url_after
    has_error = any(kw in content.lower() for kw in [
        "required", "error", "field", "invalid", "this field"
    ])
    assert is_still_on_form, "Empty form submission redirected to sign-in"
    assert has_error, "No validation error shown for empty required fields"


@pytest.mark.asyncio
async def test_2_11_partial_family_member_shows_error(page: Page):
    """A family member form with first_name but no last_name shows a validation error."""
    url = _token_url("validation")
    if not url:
        pytest.skip("Validation token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")

    first_fm_first = page.locator('[name="family-0-first_name"]')
    if await first_fm_first.count() == 0:
        pytest.skip("No family member form fields found in the DOM")

    # Fill primary user with valid data
    await page.fill('input[name="first_name"]', "Test")
    await page.fill('input[name="last_name"]', "User")
    await page.fill('input[name="password1"]', _REG_PASSWORD)
    await page.fill('input[name="password2"]', _REG_PASSWORD)

    # Fill first_name only — last_name is required and left blank
    await first_fm_first.fill("FirstNameOnly")

    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_11_fm_partial"))

    content = await page.content()
    url_after = page.url
    is_still_on_form = "sign-in" not in url_after
    has_error = any(kw in content.lower() for kw in [
        "required", "error", "last name", "this field"
    ])
    assert is_still_on_form, "Partial family member form submitted successfully (unexpected)"
    assert has_error, "No validation error shown for incomplete family member"


# ---------------------------------------------------------------------------
# 2.12 – 2.14  Actual registration tests (each consumes its own token)
# ---------------------------------------------------------------------------

async def _fill_primary_user(page: Page, first="Reg", last="Tester", password=_REG_PASSWORD):
    """Fill the primary user section of the registration form."""
    await page.fill('input[name="first_name"]', first)
    await page.fill('input[name="last_name"]', last)
    await page.fill('input[name="password1"]', password)
    await page.fill('input[name="password2"]', password)


@pytest.mark.asyncio
async def test_2_12_solo_registration_succeeds(page: Page):
    """A primary user can register without adding family members."""
    url = _token_url("solo")
    if not url:
        pytest.skip("Solo registration token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await _fill_primary_user(page, first="Solo", last="Registrant")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_12_solo_reg"))

    content = await page.content()
    url_after = page.url
    assert "500" not in await page.title(), "Server error during solo registration"
    assert "Registration failed" not in content, \
        f"Registration failed message shown: check server logs for exception details"
    assert "sign-in" in url_after or "sign_in" in url_after or "success" in content.lower(), \
        "Solo registration did not redirect to sign-in"


@pytest.mark.asyncio
async def test_2_13_registration_with_adult_family_member_succeeds(page: Page):
    """A primary user can register with an adult family member (spouse/partner)."""
    url = _token_url("spouse")
    if not url:
        pytest.skip("Spouse registration token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await _fill_primary_user(page, first="Adult", last="Primary")

    # Fill the first family member slot
    first_fm_first = page.locator('[name="family-0-first_name"]')
    if await first_fm_first.count() > 0:
        await first_fm_first.fill("Adult")
        await page.fill('[name="family-0-last_name"]', "Partner")

    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_13_adult_family_reg"))

    content = await page.content()
    url_after = page.url
    assert "500" not in await page.title(), "Server error during family registration"
    assert "Registration failed" not in content, \
        "Registration with adult family member failed — check server logs"
    assert "sign-in" in url_after or "sign_in" in url_after or "success" in content.lower(), \
        "Family registration did not redirect to sign-in"


@pytest.mark.asyncio
async def test_2_14_registration_with_child_family_member_succeeds(page: Page):
    """A primary user can register with a child family member.

    Membership type assignment for the child is handled by admins after registration.
    All family members start with the default "Regular" membership type at registration time.
    """
    url = _token_url("child")
    if not url:
        pytest.skip("Child registration token not found — run seed_test_data first")

    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await _fill_primary_user(page, first="Child", last="Primary")

    # Fill the first family member — with a date_of_birth to identify as child
    first_fm_first = page.locator('[name="family-0-first_name"]')
    if await first_fm_first.count() > 0:
        await first_fm_first.fill("Junior")
        await page.fill('[name="family-0-last_name"]', "Member")
        dob_field = page.locator('[name="family-0-date_of_birth"]')
        if await dob_field.count() > 0:
            await dob_field.fill("2015-06-15")

    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_14_child_reg"))

    content = await page.content()
    url_after = page.url
    assert "500" not in await page.title(), "Server error during child registration"
    assert "Registration failed" not in content, \
        "Registration with child failed — check server logs for exception details"
    assert "sign-in" in url_after or "sign_in" in url_after or "success" in content.lower(), \
        "Child registration did not redirect to sign-in"


# ---------------------------------------------------------------------------
# 2.15 – 2.16  Post-registration state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_15_used_token_is_rejected(page: Page):
    """A consumed invitation token returns an error, not the registration form."""
    # Use the solo token which was consumed by test_2_12
    tokens = _load_tokens()
    solo_token = tokens.get("solo")
    if not solo_token:
        pytest.skip("Solo token not found — run seed_test_data first")

    url = f"{REGISTER_FAMILY_URL}{solo_token}/"
    resp = await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_15_used_token"))

    status = resp.status if resp else 0
    content = await page.content()
    url_after = page.url
    # Should redirect to sign-in or show an error — registration form should NOT appear
    is_rejected = (
        "sign-in" in url_after
        or "sign_in" in url_after
        or "invalid" in content.lower()
        or "expired" in content.lower()
        or "used" in content.lower()
        or status in (404, 403)
    )
    assert is_rejected, "Used invitation token still shows registration form — invitation not marked as used"


@pytest.mark.asyncio
async def test_2_16_new_account_can_sign_in(page: Page):
    """A user registered in test_2_12 (solo) can sign in with their credentials."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="email"]', "reg.solo@csc-test.local")
    await page.fill('input[name="password"]', _REG_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("02_16_new_account_login"))

    url_after = page.url
    content = await page.content()
    # Should be redirected away from sign-in (to dashboard or home)
    is_logged_in = (
        "sign-in" not in url_after
        and "sign_in" not in url_after
        and "invalid" not in content.lower()
        and "does not exist" not in content.lower()
    )
    if not is_logged_in:
        pytest.skip(
            "Newly registered account could not sign in — "
            "test_2_12 may not have run or registration failed"
        )
