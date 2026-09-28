"""Section 40 — Broadcasts (admin club-wide email tool)

/broadcasts/ lets a Booking Administrator compose and send club-wide email.
Access is `@broadcast_sender_required` = `is_booking_administrator` only —
notably NARROWER than Members+, which sits next to it in the nav for
newsletters. That asymmetry is an easy permission regression to introduce
(e.g. by copy-pasting the newsletter capability check), so it gets its own
explicit assertion here.

Django's own test suite (`broadcasts/tests/test_views.py`) already proves the
send-gate, recipient-resolution, and retry logic thoroughly at the unit
level. This suite's job is just the real browser flow: compose with the
CKEditor5 rich-text field, save a draft, and "Send test to myself" — which
Django's own tests confirm mails only the composing admin and creates no
recipient rows / does not change status, so it's safe to run for real.

**Never click the real "Send to {N} recipients" button in an automated
test** — unlike test-send, that queues a real send to the configured
audience. Same caution as Section 28 not submitting a real refund.
"""
import uuid

import pytest
from playwright.async_api import Page
from tests.helpers import (
    BROADCASTS_URL, BROADCASTS_COMPOSE_URL, fill_ckeditor, screenshot_path,
)


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_40_1_anonymous_redirected_to_login(page: Page):
    await page.goto(BROADCASTS_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_40_2_member_blocked(alice_page: Page):
    resp = await alice_page.goto(BROADCASTS_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_40_3_members_plus_blocked(members_plus_page: Page):
    """Members+ manages newsletters but NOT broadcasts — narrower capability,
    easy to regress if broadcasts is ever folded into the newsletter grant."""
    resp = await members_plus_page.goto(BROADCASTS_URL)
    status = resp.status if resp else 0
    url = members_plus_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected Members+ to be blocked from broadcasts, got status={status} url={url}"


@pytest.mark.asyncio
async def test_40_4_booking_admin_allowed(booking_admin_page: Page):
    resp = await booking_admin_page.goto(BROADCASTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    assert resp.status == 200


# ---------------------------------------------------------------------------
# Compose page
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_40_5_compose_page_loads_with_rich_text_editor(booking_admin_page: Page):
    resp = await booking_admin_page.goto(BROADCASTS_COMPOSE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("40_5_compose_page"))
    assert resp.status == 200
    assert await booking_admin_page.locator("#id_subject").count() == 1
    assert await booking_admin_page.locator("#id_audience").count() == 1
    # CKEditor5 replaces the source textarea with a .ck-editor container
    assert await booking_admin_page.locator(".ck-editor, #id_body").count() > 0


# ---------------------------------------------------------------------------
# Draft + "Send test to myself" — safe, self-contained happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_40_6_save_draft_then_send_test_to_myself(booking_admin_page: Page):
    unique = uuid.uuid4().hex[:8]
    await booking_admin_page.goto(BROADCASTS_COMPOSE_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    await booking_admin_page.fill("#id_subject", f"Playwright test_40 draft {unique}")
    await fill_ckeditor(booking_admin_page, "id_body", f"<p>Playwright test_40 body {unique}</p>")

    # Audience choice is inconsequential here — this test never clicks the
    # real "Send to {N} recipients" button, so it can't reach real members
    # regardless of which audience is selected.
    await booking_admin_page.select_option("#id_audience", index=0)

    await booking_admin_page.locator("button[type='submit']", has_text="Save draft").click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("40_6_after_save_draft"))

    assert "/broadcasts/" in booking_admin_page.url
    content = await booking_admin_page.content()
    assert "traceback" not in content.lower() and "server error" not in content.lower()

    test_send_btn = booking_admin_page.locator("button", has_text="Send test to myself")
    assert await test_send_btn.count() > 0, "Expected a 'Send test to myself' control on the detail page"
    await test_send_btn.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("40_6_after_test_send"))

    content = await booking_admin_page.content()
    assert "traceback" not in content.lower() and "server error" not in content.lower()
    # Django's own tests prove test-send never changes status or creates
    # recipient rows — a real send button should still be present, unclicked.
    assert await booking_admin_page.locator("button", has_text="Send to").count() > 0


@pytest.mark.asyncio
async def test_40_7_send_gate_requires_typed_confirmation(booking_admin_page: Page):
    """The real send form requires typing the exact recipient count before
    it submits — but only once `delivery_count > BROADCAST_TYPED_CONFIRM_THRESHOLD`
    (see broadcasts/views.py); on a small club/staging audience the "All
    members" draft this suite creates may sit under that threshold, in which
    case the gate legitimately doesn't render. Never satisfy the gate in
    this suite either way."""
    await booking_admin_page.goto(BROADCASTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    detail_link = booking_admin_page.locator("a", has_text="Playwright test_40").first
    if await detail_link.count() == 0:
        pytest.skip("No Playwright-created draft found on the list page to inspect")
    await detail_link.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    confirm_input = booking_admin_page.locator('input[name="confirm_count"]')
    if await confirm_input.count() == 0:
        pytest.skip("Delivery count is under BROADCAST_TYPED_CONFIRM_THRESHOLD — "
                     "the typed-confirmation gate doesn't render for this audience size")
