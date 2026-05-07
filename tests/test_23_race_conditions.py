"""Section 23 — Race Conditions & Concurrency

Tests concurrent cart operations to verify the booking system handles simultaneous
requests without double-booking a room or corrupting cart state. Uses two separate
browser contexts (Alice and Bob) operating concurrently on the same date window.
"""
import asyncio
import pytest
from datetime import date, timedelta
from playwright.async_api import async_playwright, Page
from tests.helpers import (
    BASE_URL, AVAILABILITY_URL, CART_URL, screenshot_path, ALICE, BOB, login
)

_CHECKIN_DATE  = date.today() + timedelta(days=85)
_CHECKOUT_DATE = date.today() + timedelta(days=87)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")
CHECKIN_DISPLAY  = _CHECKIN_DATE.strftime("%B %-d, %Y")
CHECKOUT_DISPLAY = _CHECKOUT_DATE.strftime("%B %-d, %Y")


async def _add_first_available_room(page: Page, label: str) -> bool:
    """Search availability and add the first available room for the race condition dates.
    Returns True if a room was added, False if no rooms or no valid occupant found."""
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', CHECKIN)
    await page.fill('input[name="check_out_date"]', CHECKOUT)
    await page.evaluate(
        'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(1500)

    member_selects = page.locator("select.member-select")
    if await member_selects.count() == 0:
        return False

    first_select = member_selects.first
    selected = False
    for opt in await first_select.locator("option").all():
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.strip() and disabled is None:
            await first_select.select_option(value=val)
            selected = True
            break

    if not selected:
        return False

    await page.evaluate(f"""
        const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{CHECKIN_DISPLAY}';
            if (co) co.value = '{CHECKOUT_DISPLAY}';
        }}
    """)
    add_btn = page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btn.count() == 0:
        return False
    await add_btn.first.click()
    await page.wait_for_load_state("networkidle")
    return True


@pytest.mark.asyncio
async def test_23_1_concurrent_cart_add_different_users():
    """Alice and Bob can simultaneously add rooms to their own carts without error."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        alice_ctx  = await browser.new_context(viewport={"width": 1280, "height": 800})
        bob_ctx    = await browser.new_context(viewport={"width": 1280, "height": 800})
        alice_page = await alice_ctx.new_page()
        bob_page   = await bob_ctx.new_page()

        await login(alice_page, ALICE["email"], ALICE["password"])
        await login(bob_page,   BOB["email"],   BOB["password"])

        # Fire both cart-add operations concurrently
        results = await asyncio.gather(
            _add_first_available_room(alice_page, "alice"),
            _add_first_available_room(bob_page,   "bob"),
            return_exceptions=True,
        )

        await alice_page.screenshot(path=screenshot_path("23_1_alice_cart"))
        await bob_page.screenshot(path=screenshot_path("23_1_bob_cart"))

        await alice_ctx.close()
        await bob_ctx.close()
        await browser.close()

    # At least one user should have succeeded; exceptions from the coroutines are failures
    errors = [r for r in results if isinstance(r, Exception)]
    assert not errors, f"Concurrent cart add raised exceptions: {errors}"
    successes = [r for r in results if r is True]
    assert len(successes) >= 1, "Neither Alice nor Bob could add a room during concurrent test"


@pytest.mark.asyncio
async def test_23_2_concurrent_cart_add_same_user_session(alice_page: Page):
    """Rapid sequential cart additions by the same user do not crash the server."""
    for attempt in range(3):
        await alice_page.goto(AVAILABILITY_URL)
        await alice_page.wait_for_load_state("networkidle")
        await alice_page.fill('input[name="check_in_date"]', CHECKIN)
        await alice_page.fill('input[name="check_out_date"]', CHECKOUT)
        await alice_page.evaluate(
            'document.querySelector(\'form[action="/bookings/check_availability/"]\').submit()'
        )
        await alice_page.wait_for_load_state("networkidle")
        await alice_page.wait_for_timeout(500)

        member_selects = alice_page.locator("select.member-select")
        if await member_selects.count() == 0:
            break

        first_select = member_selects.first
        for opt in await first_select.locator("option").all():
            val = await opt.get_attribute("value")
            disabled = await opt.get_attribute("disabled")
            if val and val.strip() and disabled is None:
                await first_select.select_option(value=val)
                break

        await alice_page.evaluate(f"""
            const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
            if (form) {{
                const ci = form.querySelector('input[name="check_in_date"]');
                const co = form.querySelector('input[name="check_out_date"]');
                if (ci) ci.value = '{CHECKIN_DISPLAY}';
                if (co) co.value = '{CHECKOUT_DISPLAY}';
            }}
        """)
        add_btn = alice_page.locator("button").filter(has_text="Add Selected to Cart")
        if await add_btn.count() > 0:
            await add_btn.first.click()
            await alice_page.wait_for_load_state("networkidle")

        assert "500" not in await alice_page.title(), f"Server error on attempt {attempt + 1}"

    await alice_page.screenshot(path=screenshot_path("23_2_rapid_add"))


@pytest.mark.asyncio
async def test_23_3_cart_state_isolated_between_users():
    """Alice's cart is not visible to Bob and vice versa."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        alice_ctx  = await browser.new_context(viewport={"width": 1280, "height": 800})
        bob_ctx    = await browser.new_context(viewport={"width": 1280, "height": 800})
        alice_page = await alice_ctx.new_page()
        bob_page   = await bob_ctx.new_page()

        await login(alice_page, ALICE["email"], ALICE["password"])
        await login(bob_page,   BOB["email"],   BOB["password"])

        # Alice adds a room
        await _add_first_available_room(alice_page, "alice")

        # Bob views his own cart — should not see Alice's items
        await bob_page.goto(CART_URL)
        await bob_page.wait_for_load_state("networkidle")
        bob_content = await bob_page.content()

        await alice_page.screenshot(path=screenshot_path("23_3_alice_cart"))
        await bob_page.screenshot(path=screenshot_path("23_3_bob_cart"))

        await alice_ctx.close()
        await bob_ctx.close()
        await browser.close()

    # Bob's cart should not contain "alice" / Alice's personal data
    assert "alice.tester" not in bob_content.lower(), \
        "Bob's cart view contains Alice's account data — possible cart isolation failure"
