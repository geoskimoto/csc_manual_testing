"""Section 31 — Club Events Calendar"""
import pytest
from playwright.async_api import Page
from tests.helpers import EVENTS_URL, DASHBOARD_URL, BASE_URL, LOGIN_URL, screenshot_path


@pytest.mark.asyncio
async def test_31_1_public_events_page_loads(page: Page):
    """Public events page loads without a server error (no auth required)."""
    await page.goto(EVENTS_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("31_1_events_public_load"))
    assert "500" not in await page.title(), "Server error on public events page"
    content = await page.content()
    assert any(kw in content.lower() for kw in ["event", "calendar", "club"]), \
        "Public events page did not render expected content"


@pytest.mark.asyncio
async def test_31_2_public_events_calendar_renders(page: Page):
    """FullCalendar renders on the public events page."""
    await page.goto(EVENTS_URL)
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=screenshot_path("31_2_events_calendar"))

    fc = page.locator('.fc')
    assert await fc.count() > 0, "FullCalendar .fc element not found on public events page"


@pytest.mark.asyncio
async def test_31_3_public_events_page_accessible_unauthenticated(page: Page):
    """Public events page is accessible without logging in."""
    await page.goto(EVENTS_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("31_3_events_unauth_access"))
    # Should NOT be redirected to login
    assert "sign-in" not in page.url and "login" not in page.url, \
        "Public events page unexpectedly requires authentication"
    assert "500" not in await page.title(), "Server error on public events page"


@pytest.mark.asyncio
async def test_31_4_public_events_feed_returns_json(page: Page):
    """Public events JSON feed endpoint returns valid JSON."""
    feed_url = f"{BASE_URL}/events/feed/public/"
    response = await page.request.get(feed_url)
    assert response.status == 200, \
        f"Public events feed returned status {response.status}"
    content_type = response.headers.get("content-type", "")
    assert "json" in content_type, \
        f"Public events feed did not return JSON (got: {content_type})"
    data = await response.json()
    assert isinstance(data, list), "Public events feed JSON is not a list"


@pytest.mark.asyncio
async def test_31_5_member_feed_requires_auth(page: Page):
    """Member events feed requires authentication."""
    feed_url = f"{BASE_URL}/events/feed/member/"
    response = await page.request.get(feed_url, max_redirects=0)
    # Expect a redirect to login (302) or a 403
    assert response.status in (302, 301, 403), \
        f"Member events feed did not redirect unauthenticated user (got: {response.status})"


@pytest.mark.asyncio
async def test_31_6_dashboard_club_calendar_renders(alice_page: Page):
    """Member dashboard contains the embedded club events calendar."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(2000)
    await alice_page.screenshot(path=screenshot_path("31_6_dashboard_calendar"))

    calendar_div = alice_page.locator('#dashboard-club-calendar')
    assert await calendar_div.count() > 0, \
        "#dashboard-club-calendar div not found on member dashboard"


@pytest.mark.asyncio
async def test_31_7_dashboard_club_calendar_fullcalendar(alice_page: Page):
    """FullCalendar initialises inside the dashboard club events div.

    FullCalendar is loaded from CDN and initialised in a DOMContentLoaded
    handler, so we wait for the .fc element to appear rather than using a
    fixed timeout.
    """
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    # Wait for FullCalendar JS to load from CDN and initialise (up to 20s).
    # The .fc element is injected by FullCalendar after DOMContentLoaded + CDN load.
    try:
        await alice_page.wait_for_function(
            "document.querySelector('#dashboard-club-calendar .fc') !== null",
            timeout=20000,
        )
    except Exception:
        pass  # screenshot still taken; assertion below gives the clear failure message
    await alice_page.screenshot(path=screenshot_path("31_7_dashboard_fc"))

    fc = alice_page.locator('#dashboard-club-calendar .fc')
    assert await fc.count() > 0, \
        "FullCalendar .fc element not found inside #dashboard-club-calendar after 20s"


@pytest.mark.asyncio
async def test_31_8_member_feed_returns_json_when_authenticated(alice_page: Page):
    """Authenticated member can retrieve the member events JSON feed."""
    feed_url = f"{BASE_URL}/events/feed/member/"
    response = await alice_page.request.get(feed_url)
    assert response.status == 200, \
        f"Member events feed returned {response.status} for authenticated user"
    content_type = response.headers.get("content-type", "")
    assert "json" in content_type, \
        f"Member events feed did not return JSON (got: {content_type})"
    data = await response.json()
    assert isinstance(data, list), "Member events feed JSON is not a list"
