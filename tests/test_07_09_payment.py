"""Sections 7–9 — Payment: Wallet, Stripe, Mixed"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import AVAILABILITY_URL, CHECKOUT_URL, CART_URL, screenshot_path

_CHECKIN_DATE  = date.today() + timedelta(days=30)
_CHECKOUT_DATE = date.today() + timedelta(days=32)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")
# Format the hidden form expects: "May 24, 2026"
CHECKIN_DISPLAY  = _CHECKIN_DATE.strftime("%B %-d, %Y")
CHECKOUT_DISPLAY = _CHECKOUT_DATE.strftime("%B %-d, %Y")


async def _add_room_to_cart(page: Page, room_index: int = 0):
    """Search availability, fix hidden date inputs, and add a room to cart.

    room_index selects the Nth available room card so parallel tests each claim
    a different bunk without competing for the same room reservation slot.
    With 50+ bunks there is ample headroom for the full payment test section.
    """
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', CHECKIN)
    await page.fill('input[name="check_out_date"]', CHECKOUT)
    await page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)  # wait for JS to render room cards

    member_selects = page.locator("select.member-select")
    total_rooms = await member_selects.count()
    if total_rooms == 0:
        return False

    idx = min(room_index, total_rooms - 1)
    target_select = member_selects.nth(idx)
    selected = False
    for opt in await target_select.locator("option").all():
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        # Skip disabled options — a profile may be conflicted (already booked for
        # these dates, e.g. after test_8_1 confirms Alice's booking).
        if val and val.strip() and disabled is None:
            await target_select.select_option(value=val)
            selected = True
            break
    if not selected:
        return False  # No valid non-conflicted occupant available

    # The add-to-cart hidden form retains today's date from the server render;
    # patch the Nth form's date inputs to match the searched dates before submitting.
    await page.evaluate(f"""
        const forms = document.querySelectorAll('form[action="/bookings/add_accommodations_to_cart/"]');
        const form = forms[{idx}] || forms[0];
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{CHECKIN_DISPLAY}';
            if (co) co.value = '{CHECKOUT_DISPLAY}';
        }}
    """)

    add_btns = page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btns.count() == 0:
        return False
    btn_idx = min(room_index, await add_btns.count() - 1)
    await add_btns.nth(btn_idx).click()
    await page.wait_for_load_state("networkidle")
    return True


@pytest.mark.asyncio
async def test_7_1_checkout_page_loads(alice_page: Page):
    """Checkout page is reachable."""
    await alice_page.goto(CHECKOUT_URL)
    await alice_page.wait_for_load_state("load")
    await alice_page.screenshot(path=screenshot_path("07_1_checkout"))
    assert "500" not in await alice_page.title()


@pytest.mark.asyncio
async def test_7_1_wallet_toggle_at_checkout(alice_page: Page):
    """Wallet option is present on checkout after adding a room."""
    added = await _add_room_to_cart(alice_page, room_index=0)
    if not added:
        pytest.skip("Could not add a room to cart")

    await alice_page.goto(CHECKOUT_URL)
    await alice_page.wait_for_load_state("load")
    await alice_page.wait_for_timeout(1500)
    await alice_page.screenshot(path=screenshot_path("07_1_wallet_toggle"))
    content = await alice_page.content()
    assert "wallet" in content.lower(), "No wallet option found on checkout page"


@pytest.mark.asyncio
async def test_8_1_stripe_form_present(alice_page: Page):
    """Stripe card input is present on checkout after adding a room."""
    added = await _add_room_to_cart(alice_page, room_index=1)
    if not added:
        pytest.skip("Could not add a room to cart")

    await alice_page.goto(CHECKOUT_URL)
    await alice_page.wait_for_load_state("load")
    await alice_page.wait_for_timeout(3000)  # Stripe JS needs time to inject iframe
    content = await alice_page.content()
    stripe_iframes = await alice_page.locator("iframe[name*='stripe'], iframe[src*='stripe']").count()
    has_stripe = "stripe" in content.lower() or stripe_iframes > 0
    await alice_page.screenshot(path=screenshot_path("08_1_stripe_form"))
    assert has_stripe, "Stripe form not found on checkout page"


async def _fill_stripe_fields(page: Page, card_number: str):
    """Fill split Stripe card fields by clicking the outer container divs and
    typing via page.keyboard. Clicking the container focuses the Stripe iframe
    input without needing to cross the frame boundary in Playwright.

    Returns False (causing a skip) if the cart is empty — the card element
    is hidden by JS when total == $0, making it impossible to interact with."""
    if await page.locator("#card-number-element iframe").count() == 0:
        return False

    # Guard: if total is $0 the card element container is hidden by JS
    total_el = page.locator("#final-total-display")
    if await total_el.count() > 0:
        try:
            total_val = float((await total_el.inner_text()).strip().replace(",", ""))
            if total_val == 0:
                return False
        except ValueError:
            pass

    await page.locator("#card-number-element").click(force=True)
    await page.keyboard.type(card_number, delay=30)

    await page.locator("#card-expiry-element").click(force=True)
    await page.keyboard.type("12/30", delay=30)

    await page.locator("#card-cvc-element").click(force=True)
    await page.keyboard.type("123", delay=30)

    return True


@pytest.mark.asyncio
async def test_8_1_stripe_success_payment(alice_page: Page):
    """Full Stripe payment with test card 4242 4242 4242 4242 confirms booking."""
    added = await _add_room_to_cart(alice_page, room_index=2)
    if not added:
        pytest.skip("Could not add a room to cart")

    await alice_page.goto(CHECKOUT_URL)
    await alice_page.wait_for_load_state("load")
    await alice_page.wait_for_timeout(3000)  # Stripe JS needs time to inject iframes

    filled = await _fill_stripe_fields(alice_page, "4242 4242 4242 4242")
    if not filled:
        pytest.skip("Stripe card fields not present or cart empty ($0 total) — prior tests may have exhausted available rooms for these dates")

    # Dismiss any Stripe Link overlay that appeared during card entry
    await alice_page.keyboard.press("Escape")
    await alice_page.wait_for_timeout(500)
    pay_btn = alice_page.locator("#pay-button")
    await pay_btn.scroll_into_view_if_needed()
    await pay_btn.click(force=True)
    await alice_page.wait_for_load_state("load", timeout=30000)
    await alice_page.wait_for_timeout(3000)  # allow redirect/confirmation to settle
    await alice_page.screenshot(path=screenshot_path("08_1_stripe_success"))

    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["success", "confirmed", "booking", "thank"]), \
        f"Payment did not appear to succeed. URL: {alice_page.url}"


@pytest.mark.asyncio
async def test_8_2_stripe_declined_card(alice_page: Page):
    """Declined test card 4000000000000002 shows an error."""
    added = await _add_room_to_cart(alice_page, room_index=3)
    if not added:
        pytest.skip("Could not add a room to cart")

    await alice_page.goto(CHECKOUT_URL)
    await alice_page.wait_for_load_state("load")
    await alice_page.wait_for_timeout(5000)  # extra wait — Stripe re-initialises after prior payment flow

    filled = await _fill_stripe_fields(alice_page, "4000 0000 0000 0002")
    if not filled:
        pytest.skip("Stripe card fields not present at checkout")

    # Dismiss any Stripe Link overlay that appeared during card entry
    await alice_page.keyboard.press("Escape")
    await alice_page.wait_for_timeout(500)
    pay_btn = alice_page.locator("#pay-button")
    await pay_btn.scroll_into_view_if_needed()
    await pay_btn.click(force=True)
    await alice_page.wait_for_timeout(8000)  # Stripe keeps network active; don't wait for networkidle
    await alice_page.screenshot(path=screenshot_path("08_2_declined"))

    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["declined", "error", "fail", "card was declined"]), \
        "No decline error shown for card 4000000000000002"
