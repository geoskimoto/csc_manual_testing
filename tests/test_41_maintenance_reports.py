"""Section 41 — Maintenance Reports (front-of-house tool)

/maintenance-reports/ is gated by `can_manage_maintenance_reports` (Members+
"buildings manager" capability + Booking Admins). Status-only tool: no
delete, no editing of member-authored content. Default view hides Resolved
reports; `?status=all` shows everything. Setting status to Resolved
auto-stamps `resolved_at`; moving away from Resolved clears it.

No seeded fixture guarantees a report exists on staging, so the status-update
test is conditional on the list actually having a row — consistent with this
suite's existing pattern for optional/accumulated staging state (see e.g.
Section 32's skip-if-already-active-subscription).
"""
import pytest
from playwright.async_api import Page
from tests.helpers import MAINTENANCE_REPORTS_URL, screenshot_path


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_41_1_anonymous_redirected_to_login(page: Page):
    await page.goto(MAINTENANCE_REPORTS_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_41_2_member_blocked(alice_page: Page):
    resp = await alice_page.goto(MAINTENANCE_REPORTS_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


@pytest.mark.asyncio
async def test_41_3_members_plus_allowed(members_plus_page: Page):
    resp = await members_plus_page.goto(MAINTENANCE_REPORTS_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_41_4_booking_admin_allowed(booking_admin_page: Page):
    resp = await booking_admin_page.goto(MAINTENANCE_REPORTS_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    assert resp.status == 200


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_41_5_filter_form_present(members_plus_page: Page):
    await members_plus_page.goto(MAINTENANCE_REPORTS_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    await members_plus_page.screenshot(path=screenshot_path("41_5_filter_form"))
    filter_form = members_plus_page.locator('form[method="get"]')
    assert await filter_form.count() == 1
    assert await filter_form.locator('select[name="status"]').count() == 1
    assert await filter_form.locator('input[name="location"]').count() == 1


@pytest.mark.asyncio
async def test_41_6_status_all_shows_more_or_equal_rows_than_default(members_plus_page: Page):
    """?status=all must never show FEWER rows than the default (Resolved-hidden) view."""
    await members_plus_page.goto(MAINTENANCE_REPORTS_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    default_rows = await members_plus_page.locator("table tbody tr").count()

    await members_plus_page.goto(f"{MAINTENANCE_REPORTS_URL}?status=all")
    await members_plus_page.wait_for_load_state("networkidle")
    all_rows = await members_plus_page.locator("table tbody tr").count()

    assert all_rows >= default_rows, (
        f"?status=all showed fewer rows ({all_rows}) than the default view ({default_rows})"
    )


# ---------------------------------------------------------------------------
# Status update (conditional on at least one row existing)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_41_7_status_update_round_trips_without_error(booking_admin_page: Page):
    await booking_admin_page.goto(f"{MAINTENANCE_REPORTS_URL}?status=all")
    await booking_admin_page.wait_for_load_state("networkidle")

    row_forms = booking_admin_page.locator('form[method="post"]')
    if await row_forms.count() == 0:
        pytest.skip("No maintenance report rows on staging to exercise a status update against")

    row_form = row_forms.first
    status_select = row_form.locator('select[name="status"]')
    current = await status_select.input_value()
    # Toggle to a different status and back, so the round trip is a no-op by
    # the time the test finishes (mirrors the non-mutating spirit used
    # elsewhere for shared staging fixtures).
    other = "In Progress" if current != "In Progress" else "New"

    await status_select.select_option(other)
    await row_form.locator('button[type="submit"]').click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("41_7_after_status_change"))
    content = await booking_admin_page.content()
    assert "traceback" not in content.lower() and "server error" not in content.lower()

    # Restore original status
    await booking_admin_page.goto(f"{MAINTENANCE_REPORTS_URL}?status=all")
    await booking_admin_page.wait_for_load_state("networkidle")
    row_form = booking_admin_page.locator('form[method="post"]').first
    await row_form.locator('select[name="status"]').select_option(current)
    await row_form.locator('button[type="submit"]').click()
    await booking_admin_page.wait_for_load_state("networkidle")
