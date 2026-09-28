"""Section 42 — Profile Integrity admin detail page

/user/admin/profile-integrity/ is Financial-Admin-only (stricter than most
booking-admin tools, since findings can expose family/PII relationships).
Its dismiss/undismiss controls are real browser JS: a `fetch()` POST from a
button click, not a form submit — Django's own test suite covers the
service-layer logic, but this real click -> fetch -> reload round trip is
something only a browser-driven test can exercise.

On success the page calls `location.reload()` itself (async, after the fetch
resolves) — wrap the click in `expect_navigation()` rather than
click-then-wait_for_load_state. On failure it raises a blocking `alert()`,
so a dialog handler is registered before clicking either button.

No dismiss/undismiss test asserts a *specific* finding exists — this suite
has no fixture that guarantees one, so happy-path round trips skip gracefully
when the page currently has zero live findings.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import PROFILE_INTEGRITY_URL, screenshot_path


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_42_1_anonymous_redirected_to_login(page: Page):
    await page.goto(PROFILE_INTEGRITY_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_42_2_member_blocked(alice_page: Page):
    resp = await alice_page.goto(PROFILE_INTEGRITY_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_42_3_booking_admin_blocked(booking_admin_page: Page):
    """Stricter than most admin tools: Booking Admins are NOT sufficient here,
    only Financial Administrators (findings can expose PII/family data)."""
    resp = await booking_admin_page.goto(PROFILE_INTEGRITY_URL)
    status = resp.status if resp else 0
    url = booking_admin_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected Booking Admin to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_42_4_financial_admin_allowed(financial_admin_page: Page):
    resp = await financial_admin_page.goto(PROFILE_INTEGRITY_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("42_4_profile_integrity_page"))
    assert resp.status == 200


# ---------------------------------------------------------------------------
# Dismiss / undismiss round trip (conditional on a live finding existing)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_42_5_dismiss_then_undismiss_round_trips(financial_admin_page: Page):
    financial_admin_page.on("dialog", lambda d: d.accept())
    await financial_admin_page.goto(PROFILE_INTEGRITY_URL)
    await financial_admin_page.wait_for_load_state("networkidle")

    dismiss_btn = financial_admin_page.locator(".dismiss-btn").first
    if await dismiss_btn.count() == 0:
        pytest.skip("No live (non-dismissed) profile integrity findings to exercise dismiss against")

    finding_row = dismiss_btn.locator("xpath=ancestor::li[1]")
    finding_id = await finding_row.get_attribute("id")

    async with financial_admin_page.expect_navigation():
        await dismiss_btn.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("42_5_after_dismiss"))

    # The same finding id should now appear under the dismissed/collapsed section
    dismissed_section = financial_admin_page.locator("#dismissed-findings")
    assert await dismissed_section.locator(f"#{finding_id}").count() == 1, \
        "Dismissed finding should now appear in the dismissed-findings section"

    # #dismissed-findings is a Bootstrap .collapse, closed by default — its
    # contents are not visible/clickable until the toggle expands it.
    await financial_admin_page.locator('[data-bs-target="#dismissed-findings"]').click()
    await financial_admin_page.wait_for_selector("#dismissed-findings.show", timeout=5000)

    undismiss_btn = dismissed_section.locator(f"#{finding_id} .undismiss-btn")
    assert await undismiss_btn.count() == 1
    async with financial_admin_page.expect_navigation():
        await undismiss_btn.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("42_5_after_undismiss"))

    # Back to a live (non-dismissed) finding
    assert await financial_admin_page.locator(f"#{finding_id} .dismiss-btn").count() == 1, \
        "Finding should be back among live findings after undismiss"
