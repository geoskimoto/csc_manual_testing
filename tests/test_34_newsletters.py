"""Section 34 — Members+ Role & Newsletter Management

Members+ is a capability-gated role between Member and Booking Administrator.
Its only current gated feature is newsletter management (can_manage_newsletters()
in userauths/permissions.py — booking admins also have this capability). Regular
members can view published newsletters but not manage them.

Test data: seed_test_data creates members.plus@csc-test.local (Members+ group,
not staff, no booking-admin access) and a published "Seed Test Issue" newsletter.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import NEWSLETTERS_URL, NEWSLETTERS_MANAGE_URL, screenshot_path


@pytest.mark.asyncio
async def test_34_1_newsletters_page_loads_for_member(alice_page: Page):
    """Any logged-in member can view the newsletters page."""
    resp = await alice_page.goto(NEWSLETTERS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("34_1_newsletters_member"))
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    content = await alice_page.content()
    assert "newsletter" in content.lower(), "Newsletters page missing expected heading"


@pytest.mark.asyncio
async def test_34_2_seeded_issue_visible_to_member(alice_page: Page):
    """The seeded published newsletter appears as the featured/latest issue."""
    await alice_page.goto(NEWSLETTERS_URL)
    await alice_page.wait_for_load_state("networkidle")
    content = await alice_page.content()
    assert "seed test issue" in content.lower(), \
        "Seeded newsletter 'Seed Test Issue' not visible on newsletters page"
    read_link = alice_page.locator("a", has_text="Read Newsletter")
    assert await read_link.count() > 0, "No 'Read Newsletter' link found for featured issue"


@pytest.mark.asyncio
async def test_34_3_regular_member_has_no_manage_link(alice_page: Page):
    """Regular members do not see a 'Manage' button on the newsletters page."""
    await alice_page.goto(NEWSLETTERS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("34_3_no_manage_link"))
    manage_link = alice_page.locator("a", has_text="Manage").filter(
        has=alice_page.locator("i.bi-gear")
    )
    assert await manage_link.count() == 0, \
        "Regular member should not see the newsletter Manage button"


@pytest.mark.asyncio
async def test_34_4_manage_page_blocked_for_regular_member(alice_page: Page):
    """A regular member is blocked (403) from the newsletter management page."""
    resp = await alice_page.goto(NEWSLETTERS_MANAGE_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    await alice_page.screenshot(path=screenshot_path("34_4_manage_blocked"))
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked from manage page, got status={status} url={url}"


@pytest.mark.asyncio
async def test_34_5_manage_page_loads_for_members_plus(members_plus_page: Page):
    """A Members+ user (not a booking admin) can reach the newsletter management page."""
    resp = await members_plus_page.goto(NEWSLETTERS_MANAGE_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    await members_plus_page.screenshot(path=screenshot_path("34_5_manage_loads"))
    assert resp.status == 200, f"Members+ user should reach manage page, got {resp.status}"
    content = await members_plus_page.content()
    assert "manage newsletters" in content.lower()


@pytest.mark.asyncio
async def test_34_6_manage_page_lists_seeded_issue(members_plus_page: Page):
    """Manage page's issue table shows the seeded newsletter with a Published badge."""
    await members_plus_page.goto(NEWSLETTERS_MANAGE_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    content = await members_plus_page.content()
    await members_plus_page.screenshot(path=screenshot_path("34_6_manage_table"))
    assert "seed test issue" in content.lower(), "Seeded newsletter not listed in manage table"
    row = members_plus_page.locator("tr", has_text="Seed Test Issue")
    assert await row.locator(".badge.bg-success", has_text="Published").count() > 0, \
        "Seeded newsletter should show a 'Published' badge"


@pytest.mark.asyncio
async def test_34_7_upload_form_has_expected_fields(members_plus_page: Page):
    """The newsletter upload form exposes all NewsletterForm fields."""
    await members_plus_page.goto(NEWSLETTERS_MANAGE_URL)
    await members_plus_page.wait_for_load_state("networkidle")
    await members_plus_page.screenshot(path=screenshot_path("34_7_upload_form"))
    for field_name in ["title", "issue_date", "pdf", "cover_image", "description", "is_published"]:
        field = members_plus_page.locator(f'[name="{field_name}"]')
        assert await field.count() > 0, f"Newsletter form missing field: {field_name}"


@pytest.mark.asyncio
async def test_34_8_admin_tools_shows_only_non_booking_admin_items_for_members_plus(members_plus_page: Page):
    """A Members+ user who is not a booking admin sees only the items gated by
    their own capabilities, never anything gated on `is_booking_administrator`.

    The exact item set has grown since this test was first written (Members+
    has since gained Club Events, Maintenance Reports, and Waiver Compliance
    capabilities, and `can_manage_events` alone renders two items — Create
    Event and Manage Events) — asserting on the specific expected texts
    rather than a bare count means the next capability grant doesn't silently
    break this test again the same way.
    """
    await members_plus_page.goto(NEWSLETTERS_URL)
    await members_plus_page.wait_for_load_state("networkidle")

    admin_tools_btn = members_plus_page.locator("button", has_text="Admin Tools")
    assert await admin_tools_btn.count() > 0, "Members+ user should see an Admin Tools dropdown"

    dropdown = members_plus_page.locator(".dropdown-menu.dropdown-menu-lg-end")
    items = dropdown.locator("li a.dropdown-item")
    count = await items.count()
    await members_plus_page.screenshot(path=screenshot_path("34_8_admin_tools_dropdown"))

    texts = [t.lower() for t in await items.all_inner_texts()]
    expected = [
        "financial dashboard", "manage newsletters", "create event",
        "manage events", "maintenance reports", "waiver compliance",
    ]
    for label in expected:
        assert any(label in t for t in texts), f"Expected '{label}' in Members+ Admin Tools, got {texts}"
    assert count == len(expected), (
        f"Expected exactly {len(expected)} Admin Tools items for Members+, found {count}: {texts}"
    )

    booking_admin_only = ["admin dashboard", "send invitations", "invoice management", "admin alert settings"]
    for label in booking_admin_only:
        assert not any(label in t for t in texts), \
            f"Members+ should never see booking-admin-only item '{label}'"
