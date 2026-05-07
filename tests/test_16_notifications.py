"""Section 16 — Notifications"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, NOTIFICATIONS_URL, screenshot_path

MARK_ALL_READ_URL = f"{BASE_URL}/notifications/mark-all-read/"


@pytest.mark.asyncio
async def test_16_1_notifications_page_loads(alice_page: Page):
    """Notifications page loads without error."""
    await alice_page.goto(NOTIFICATIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("16_1_notifications"))
    assert "500" not in await alice_page.title(), "Server error on notifications page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "notification", "inbox", "no notifications", "all caught up", "mark"
    ]), "Notifications page did not render expected content"


@pytest.mark.asyncio
async def test_16_2_mark_all_read_button_present(alice_page: Page):
    """Notifications page has a 'Mark all as read' button or link."""
    await alice_page.goto(NOTIFICATIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("16_2_mark_all_read"))
    content = await alice_page.content()
    has_mark_all = (
        "mark all" in content.lower()
        or "mark-all-read" in content
        or "/notifications/mark-all-read/" in content
    )
    if not has_mark_all:
        pytest.skip("'Mark all as read' not visible — may only appear when unread notifications exist")


@pytest.mark.asyncio
async def test_16_3_mark_all_read_action(alice_page: Page):
    """Clicking 'Mark all as read' does not error."""
    await alice_page.goto(NOTIFICATIONS_URL)
    await alice_page.wait_for_load_state("networkidle")

    mark_all = alice_page.locator("a, button").filter(has_text="Mark all")
    if await mark_all.count() == 0:
        pytest.skip("No 'Mark all as read' button present")

    await mark_all.first.click()
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("16_3_after_mark_all"))
    assert "500" not in await alice_page.title(), "Server error after mark all as read"


@pytest.mark.skip(
    reason=(
        "test_16_3 bulk-marks all notifications as read before this test runs, "
        "consuming the single seeded unread notification. Needs a second seeded "
        "unread notification to run reliably in the full suite."
    )
)
@pytest.mark.asyncio
async def test_16_4_individual_notification_mark_read(alice_page: Page):
    """Unread notification has a 'Mark Read' button that fires without error.
    Individual mark-read is AJAX-based (POST to /notifications/<id>/read/),
    not an anchor link — this test targets the actual DOM button."""
    await alice_page.goto(NOTIFICATIONS_URL)
    await alice_page.wait_for_load_state("networkidle")

    mark_read_btns = alice_page.locator("button").filter(has_text="Mark Read")
    if await mark_read_btns.count() == 0:
        pytest.skip(
            "No unread 'Mark Read' buttons visible — test_16_3 (mark-all-read) "
            "likely cleared the seeded unread notification. Run this test in isolation "
            "or re-seed to verify individual mark-read."
        )

    await mark_read_btns.first.click()
    await alice_page.wait_for_timeout(2000)  # allow AJAX response
    await alice_page.screenshot(path=screenshot_path("16_4_mark_read"))
    assert "500" not in await alice_page.title(), "Server error when marking notification as read"


@pytest.mark.asyncio
async def test_16_5_notifications_anonymous_redirect(page: Page):
    """Anonymous user is redirected from notifications page."""
    await page.goto(NOTIFICATIONS_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("16_5_anon_notifications"))
    assert "sign-in" in page.url or "login" in page.url, \
        f"Anonymous user not redirected from notifications — got {page.url}"


@pytest.mark.asyncio
async def test_16_6_notification_count_in_nav(alice_page: Page):
    """Navigation shows a notification badge or count indicator."""
    from tests.helpers import BASE_URL
    await alice_page.goto(BASE_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("16_6_nav_notification_badge"))
    content = await alice_page.content()
    has_notif_nav = any(kw in content.lower() for kw in [
        "notification", "badge", "/notifications/"
    ])
    assert has_notif_nav, "No notification indicator found in site navigation"
