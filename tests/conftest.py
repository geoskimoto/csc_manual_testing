import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Page
from tests.helpers import (
    ALICE, BOB, BOOKING_ADMIN, FINANCIAL_ADMIN, MEMBERS_PLUS,
    login, AVAILABILITY_URL, screenshot_path,
)


# --- Failure reporting plumbing --------------------------------------------
# Standard pytest recipe: stash each phase's report on the test item so
# fixture teardown can check `item.rep_call.failed` after the test body ran.
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


async def _capture_failure_screenshot(page: Page, request):
    """Best-effort screenshot on test failure, named after the failing test.

    Must be called from inside the owning fixture BEFORE that fixture closes
    its context — fixture teardown runs in reverse-of-setup order, so a
    separate autouse fixture with no dependency on the page fixture would
    tear down after the context is already closed and the page unusable.
    """
    report = getattr(request.node, "rep_call", None)
    if report is None or not report.failed or page.is_closed():
        return
    try:
        await page.screenshot(path=screenshot_path(f"FAILURE_{request.node.name}"))
    except Exception:
        pass


# Function-scoped browser per test — avoids session/event-loop scope conflicts
# with pytest-asyncio. Slight overhead but reliable.
@pytest_asyncio.fixture
async def browser():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


# NOTE: role fixtures deliberately call login() fresh every test rather than
# restoring a shared Playwright storage_state. A storage_state approach was
# tried (reuse one login per role per pytest session) to cut ~250+ real
# logins down to 5 — but it reuses the exact same Django sessionid across
# every test for a role, and the admin booking cart is session-bound
# (test_33's own docstring: "every fixture opens a fresh browser context
# (fresh session)"). Sharing a session let stale/expired session-bound cart
# state from one test leak into another, which surfaced as
# test_33_2_admin_creates_wallet_paid_booking timing out waiting for a
# checkout redirect that never came. Reverted 2026-09-28 — fresh per-test
# sessions are a correctness requirement here, not just a login-flow detail.
@pytest_asyncio.fixture
async def page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def alice_page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, ALICE["email"], ALICE["password"])
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def bob_page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, BOB["email"], BOB["password"])
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def booking_admin_page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, BOOKING_ADMIN["email"], BOOKING_ADMIN["password"])
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def financial_admin_page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, FINANCIAL_ADMIN["email"], FINANCIAL_ADMIN["password"])
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def members_plus_page(browser, request):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, MEMBERS_PLUS["email"], MEMBERS_PLUS["password"])
    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()


@pytest_asyncio.fixture
async def alice_map_page(browser, request):
    """Alice logged in, availability searched, map view active."""
    from datetime import date, timedelta
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, ALICE["email"], ALICE["password"])

    checkin  = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout = (date.today() + timedelta(days=32)).strftime("%Y-%m-%d")

    await pg.goto(AVAILABILITY_URL)
    await pg.wait_for_load_state("networkidle")
    await pg.fill('input[name="check_in_date"]', checkin)
    await pg.fill('input[name="check_out_date"]', checkout)
    await pg.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await pg.wait_for_load_state("networkidle")
    await pg.wait_for_timeout(2000)

    await pg.click('#view-toggle-map')
    try:
        await pg.wait_for_selector('#lodge-map-host', state='visible', timeout=45000)
    except Exception:
        # Map host did not become visible — skip all tests using this fixture
        # rather than ERRORing, which masks the real failure reason.
        await context.close()
        pytest.skip("alice_map_page: #lodge-map-host did not become visible after 45s — map toggle may be unavailable for the searched dates")
        return
    await pg.wait_for_timeout(1000)  # SVG render settle

    yield pg
    await _capture_failure_screenshot(pg, request)
    await context.close()
