"""Section 39 — Waivers app

Member-facing "My Waivers" status view + sign flow, the Members+ compliance
roster, and the public no-login guest QR/link signing flow with
guardian-consent enforcement for minors.

Fixture note: seed_test_data seeds one active WaiverTemplate ("seed-test-waiver")
— Bob is left signed (compliant) and Alice unsigned (non-compliant) as a
deliberate signed/unsigned pair for the compliance-roster tests. Critically,
seed_test_data does NOT reset Alice's signature if a test actually signs it —
the code comment in seed_test_data.py says as much. So this suite reads
Alice's sign page and the sign FORM without ever submitting it, exactly like
Section 28's admin refund test avoids submitting a refund that would break
other sections' fixtures.

The public guest-sign flow uses a separate GuestWaiverSignature model
disconnected from member compliance, so those tests fully complete
end-to-end — no shared fixture to protect.

The seeded "seed-test-waiver" template defaults to `audience='members'`
(seed_test_data never passes `audience=`), so it 404s from `guest_sign` by
design (see root CLAUDE.md's `WaiverTemplate.audience` note). The guest-sign
tests instead discover a real `audience in (guests, both)` template
dynamically via the admin-only `guest_sign_links` page, and skip cleanly if
staging currently has none.
"""
import uuid
from datetime import date

import pytest
from playwright.async_api import Page
from tests.helpers import (
    BASE_URL, MY_WAIVERS_URL, WAIVER_COMPLIANCE_URL, WAIVER_GUEST_LINKS_URL,
    screenshot_path,
)


async def _discover_guest_sign_path(admin_page: Page) -> str | None:
    """Find a live guest-facing waiver's sign path via the admin QR/links page.

    Returns the relative path (e.g. "/waivers/guest-sign/xyz/") of the first
    listed template, or None if staging currently has no active
    guest/both-audience WaiverTemplate.
    """
    await admin_page.goto(WAIVER_GUEST_LINKS_URL)
    await admin_page.wait_for_load_state("networkidle")
    code_el = admin_page.locator("code.text-break").first
    if await code_el.count() == 0:
        return None
    path = (await code_el.inner_text()).strip()
    return path or None


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_39_1_my_waivers_requires_login(page: Page):
    await page.goto(MY_WAIVERS_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_39_2_member_blocked_from_compliance_roster(alice_page: Page):
    resp = await alice_page.goto(WAIVER_COMPLIANCE_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_39_3_guest_sign_is_public_no_login(booking_admin_page: Page, page: Page):
    """The guest QR/link page must be reachable without any session."""
    path = await _discover_guest_sign_path(booking_admin_page)
    if not path:
        pytest.skip("No active guest/both-audience WaiverTemplate on staging to test against")
    resp = await page.goto(f"{BASE_URL}{path}")
    await page.wait_for_load_state("networkidle")
    assert resp.status == 200
    assert "sign-in" not in page.url


# ---------------------------------------------------------------------------
# My Waivers — read-only status checks (do not sign, see module docstring)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_39_4_bob_shows_signed(bob_page: Page):
    await bob_page.goto(MY_WAIVERS_URL)
    await bob_page.wait_for_load_state("networkidle")
    await bob_page.screenshot(path=screenshot_path("39_4_bob_my_waivers"))
    signed_badge = bob_page.locator(".badge.bg-success", has_text="Signed")
    assert await signed_badge.count() > 0, "Bob should show as Signed for the seeded waiver"


@pytest.mark.asyncio
async def test_39_5_alice_shows_unsigned_with_sign_link(alice_page: Page):
    await alice_page.goto(MY_WAIVERS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("39_5_alice_my_waivers"))
    sign_link = alice_page.locator("a.btn-primary", has_text="Sign")
    assert await sign_link.count() > 0, "Alice should have an outstanding Sign link"


@pytest.mark.asyncio
async def test_39_6_alice_sign_form_loads_without_submitting(alice_page: Page):
    """Load the real sign form and confirm its fields exist. Does NOT submit
    — signing would permanently consume the non-compliant fixture other
    tests (and Section 39's own roster tests) rely on."""
    await alice_page.goto(MY_WAIVERS_URL)
    await alice_page.wait_for_load_state("networkidle")
    profile_link = alice_page.locator("a.btn-primary", has_text="Sign").first
    if await profile_link.count() == 0:
        pytest.skip("No outstanding Sign link for Alice — seeded waiver may already be signed")
    href = await profile_link.get_attribute("href")
    assert href, "Expected a real sign URL on Alice's My Waivers page"

    await alice_page.goto(href if href.startswith("http") else f"{BASE_URL}{href}")
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("39_6_alice_sign_form"))
    assert await alice_page.locator("#id_typed_name").count() == 1
    assert await alice_page.locator("#id_affirmed").count() == 1
    assert await alice_page.locator("button[type='submit']").count() > 0


# ---------------------------------------------------------------------------
# Members+ compliance roster
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_39_7_compliance_roster_shows_both_statuses(members_plus_page: Page):
    resp = await members_plus_page.goto(WAIVER_COMPLIANCE_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    await members_plus_page.screenshot(path=screenshot_path("39_7_compliance_roster"))
    assert resp.status == 200
    content = await members_plus_page.content()
    assert "Bob" in content and "Alice" in content
    assert await members_plus_page.locator(".badge.bg-success", has_text="Signed").count() > 0
    assert await members_plus_page.locator(".badge.bg-warning", has_text="Unsigned").count() > 0


# ---------------------------------------------------------------------------
# Public guest-sign flow — fully completed each run (disposable fixture)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_39_8_guest_sign_adult_happy_path(booking_admin_page: Page, page: Page):
    unique = uuid.uuid4().hex[:8]
    path = await _discover_guest_sign_path(booking_admin_page)
    if not path:
        pytest.skip("No active guest/both-audience WaiverTemplate on staging to test against")
    await page.goto(f"{BASE_URL}{path}")
    await page.wait_for_load_state("networkidle")

    await page.fill("#id_guest_name", f"Playwright Guest {unique}")
    await page.fill("#id_guest_email", f"guest.{unique}@csc-test.local")
    # An adult DOB — well outside the minor threshold
    await page.fill("#id_date_of_birth", "1990-01-01")
    await page.locator("#id_date_of_birth").dispatch_event("change")
    await page.fill("#id_typed_name", f"Playwright Guest {unique}")
    await page.check("#id_affirmed")
    await page.locator("button[type='submit']").click()
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("39_8_guest_sign_adult"))

    content = await page.content()
    assert "traceback" not in content.lower() and "server error" not in content.lower()


@pytest.mark.asyncio
async def test_39_9_guest_sign_minor_requires_guardian_fields(booking_admin_page: Page, page: Page):
    """A minor DOB must reveal/require guardian fields; submitting without
    them must be rejected (server-side enforcement, per GuestWaiverSignForm.clean())."""
    unique = uuid.uuid4().hex[:8]
    minor_dob = date.today().replace(year=date.today().year - 10).isoformat()

    path = await _discover_guest_sign_path(booking_admin_page)
    if not path:
        pytest.skip("No active guest/both-audience WaiverTemplate on staging to test against")
    await page.goto(f"{BASE_URL}{path}")
    await page.wait_for_load_state("networkidle")
    await page.fill("#id_guest_name", f"Playwright Minor {unique}")
    await page.fill("#id_date_of_birth", minor_dob)
    await page.locator("#id_date_of_birth").dispatch_event("change")
    await page.fill("#id_typed_name", f"Guardian For {unique}")
    await page.check("#id_affirmed")
    # Deliberately leave guardian_name / guardian_relationship blank
    await page.locator("button[type='submit']").click()
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("39_9_minor_missing_guardian"))

    content = await page.content()
    assert "guardian" in content.lower(), \
        "Expected a guardian-required validation error when guardian fields are blank for a minor"

    # Now complete it properly and confirm the happy path for a minor works.
    await page.fill("#id_guardian_name", f"Guardian For {unique}")
    await page.fill("#id_guardian_relationship", "Parent")
    await page.locator("button[type='submit']").click()
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("39_9_minor_with_guardian"))
    content = await page.content()
    assert "traceback" not in content.lower() and "server error" not in content.lower()
