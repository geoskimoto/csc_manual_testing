import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Page
from tests.helpers import ALICE, BOB, BOOKING_ADMIN, FINANCIAL_ADMIN, login, AVAILABILITY_URL


# Function-scoped browser per test — avoids session/event-loop scope conflicts
# with pytest-asyncio. Slight overhead but reliable.
@pytest_asyncio.fixture
async def browser():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest_asyncio.fixture
async def page(browser):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    yield pg
    await context.close()


@pytest_asyncio.fixture
async def alice_page(browser):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, ALICE["email"], ALICE["password"])
    yield pg
    await context.close()


@pytest_asyncio.fixture
async def bob_page(browser):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, BOB["email"], BOB["password"])
    yield pg
    await context.close()


@pytest_asyncio.fixture
async def booking_admin_page(browser):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, BOOKING_ADMIN["email"], BOOKING_ADMIN["password"])
    yield pg
    await context.close()


@pytest_asyncio.fixture
async def financial_admin_page(browser):
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, FINANCIAL_ADMIN["email"], FINANCIAL_ADMIN["password"])
    yield pg
    await context.close()


@pytest_asyncio.fixture
async def alice_map_page(browser):
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
    await pg.wait_for_selector('#lodge-map-host', state='visible')
    await pg.wait_for_timeout(1000)  # SVG render settle

    yield pg
    await context.close()
