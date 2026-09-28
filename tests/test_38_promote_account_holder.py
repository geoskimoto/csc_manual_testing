"""Section 38 — Promote-to-Account-Holder (admin tool)

/user/admin/promote-profile/ lets a Booking Administrator invite the person
behind an existing dependent Profile (an adult family member with no login
yet) to create their own account, preserving their existing history. The
dropdown excludes minors, family-less profiles, and profiles that already
have a pending invitation — enforced server-side in
`userauths.promotion_services.send_promotion_invitation()`.

The public acceptance page (`/user/promote/<token>/`) is reachable with no
login. This suite has no way to read the real invitation email sent to
`delivery_email` (staging doesn't expose sent mail to Playwright), so the
happy-path acceptance flow is NOT automated here — only the admin-side
picker/send flow and the public page's handling of a bogus/expired token,
which is fully testable without a real token. See CLAUDE.md's "Not
Automated" section for the equivalent existing carve-out on period locking.
"""
import uuid

import pytest
from playwright.async_api import Page
from tests.helpers import PROMOTE_PROFILE_URL, PROMOTE_ACCEPT_URL_STEM, screenshot_path


# ---------------------------------------------------------------------------
# Access control — admin picker
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_38_1_anonymous_redirected_to_login(page: Page):
    await page.goto(PROMOTE_PROFILE_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_38_2_member_blocked(alice_page: Page):
    resp = await alice_page.goto(PROMOTE_PROFILE_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_38_3_booking_admin_sees_picker(booking_admin_page: Page):
    resp = await booking_admin_page.goto(PROMOTE_PROFILE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("38_3_promote_picker"))
    assert resp.status == 200
    assert await booking_admin_page.locator("#profile_id").count() == 1
    assert await booking_admin_page.locator("#delivery_email").count() == 1


# ---------------------------------------------------------------------------
# Send flow — tolerant of "already pending" from a prior run, since this
# suite has no way to clear stale ProfilePromotionInvitation rows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_38_4_send_invitation_to_first_eligible_profile(booking_admin_page: Page):
    await booking_admin_page.goto(PROMOTE_PROFILE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    options = await booking_admin_page.locator("#profile_id option").all()
    eligible_value = None
    for opt in options:
        val = await opt.get_attribute("value")
        if val:
            eligible_value = val
            break
    if eligible_value is None:
        pytest.skip("No eligible profile in the Promote-to-Account-Holder dropdown — "
                    "needs an adult (18+) dependent with no login and no pending invite")

    await booking_admin_page.select_option("#profile_id", value=eligible_value)
    unique_email = f"promote.test.{uuid.uuid4().hex[:8]}@csc-test.local"
    await booking_admin_page.fill("#delivery_email", unique_email)
    await booking_admin_page.locator("button[type='submit']").click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("38_4_after_send"))

    content = (await booking_admin_page.content()).lower()
    # "already pending" is a known, non-error outcome shown as a warning —
    # only a hard validation/server error is a real failure here.
    assert "traceback" not in content and "server error" not in content


# ---------------------------------------------------------------------------
# Public acceptance page — bogus token handling (no real token available)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_38_5_public_acceptance_page_invalid_token_is_graceful(page: Page):
    """A bogus/expired token must show a friendly message, never a 500."""
    bogus_token = uuid.uuid4()
    resp = await page.goto(f"{PROMOTE_ACCEPT_URL_STEM}{bogus_token}/")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("38_5_invalid_token"))
    status = resp.status if resp else 0
    assert status != 500, "Invalid promotion token should not 500"
    content = await page.content()
    assert "traceback" not in content.lower()
