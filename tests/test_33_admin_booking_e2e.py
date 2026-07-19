"""Section 33 — Admin Booking Creation + Refund, End-to-End

Fills the two known gaps in admin coverage (sections 12/13/28 are smoke-level):
  1. An admin actually CREATES a booking through the full flow:
     availability search → room assignment → cart → checkout → wallet payment
     → booking-success page.
  2. An admin actually EXECUTES a refund (full amount, to wallet) on that
     booking via the Manage Bookings refund modal — including the confirm()
     dialog and the async wallet-dropdown population.

Design constraints honored:
  - We NEVER touch the seeded bookings (test_28 depends on Alice's seeded
    confirmed booking keeping its refund button). This section creates its own
    booking and refunds it, leaving the DB net-neutral: the member's wallet is
    debited by the booking total and credited back in full by the refund.
  - The admin cart is session-bound and every fixture opens a fresh browser
    context (fresh session), so search → cart → checkout → pay must run inside
    a single test (33_2). Later tests verify server-side state only.
  - Wallet payment (not Stripe) keeps the flow synchronous — the server
    confirms the booking in admin_create_payment_intent and the page redirects
    straight to booking-success, no webhook or card iframe involved.

Member selection: prefers Bob, falls back to Alice (both are seeded with
$8,000 wallets). If neither appears in the room-assignment dropdown for the
chosen dates (e.g. duplicate-occupant prevention), the section skips.

State is shared between tests via the module-level STATE dict, matching the
chained-test pattern of test_32.
"""
import re
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import (
    BOB, ALICE, WALLET_URL, login,
    ADMIN_AVAIL_URL, ADMIN_CART_URL, ADMIN_CHECKOUT_URL, ADMIN_MANAGE_URL,
    screenshot_path,
)

# Dates inside the default 21-day booking window so no admin override toggle
# is needed. Offset from the seeded/map-test dates (+30..32) and test_12's
# (+70..72) to reduce occupant-conflict interference.
_CHECKIN_DATE  = date.today() + timedelta(days=10)
_CHECKOUT_DATE = date.today() + timedelta(days=12)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")

# Candidate members in preference order — both seeded with wallet funds.
CANDIDATES = [("bob", BOB), ("alice", ALICE)]

# Shared state across the chained tests in this module.
STATE = {
    "start_balances": {},   # {"bob": Decimal-as-float, "alice": ...}
    "member_key": None,     # "bob" or "alice" — whoever got booked
    "booking_id": None,     # ShortUUID from the booking-success URL
    "total": None,          # booking total charged to the wallet
    "refunded": False,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _read_wallet_balance(page: Page) -> float:
    """Read the balance from the member wallet page (h2.display-4 → '$8000.00')."""
    await page.goto(WALLET_URL)
    await page.wait_for_load_state("networkidle")
    text = await page.locator("h2.display-4").first.inner_text()
    match = re.search(r"\$\s*([\d,]+\.?\d*)", text)
    assert match, f"Could not parse wallet balance from {text!r}"
    return float(match.group(1).replace(",", ""))


def _require(key: str, reason: str):
    """Skip the current test if an earlier chained step didn't record `key`."""
    if not STATE.get(key):
        pytest.skip(reason)


# ---------------------------------------------------------------------------
# 33.1 — Baseline: capture both candidate members' wallet balances
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_1_capture_member_start_balances(browser):
    """Record Bob's and Alice's wallet balances before any booking is made."""
    for key, creds in CANDIDATES:
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        pg = await context.new_page()
        await login(pg, creds["email"], creds["password"])
        try:
            STATE["start_balances"][key] = await _read_wallet_balance(pg)
        finally:
            await context.close()
    assert STATE["start_balances"], "Could not read any member wallet balance"


# ---------------------------------------------------------------------------
# 33.2 — Full admin booking creation flow (single session)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_2_admin_creates_wallet_paid_booking(booking_admin_page: Page):
    """Admin books a bunk for Bob (or Alice), pays from the member's wallet,
    and lands on the booking-success page."""
    pg = booking_admin_page

    # -- Step 1: availability search -------------------------------------
    await pg.goto(ADMIN_AVAIL_URL)
    await pg.wait_for_load_state("networkidle")
    await pg.fill("#check_in_date", CHECKIN)
    await pg.fill("#check_out_date", CHECKOUT)
    await pg.click("#availability-form button[type='submit']")
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_2a_avail_results"))

    selects = pg.locator("#room-assignment-form select.member-select")
    if await selects.count() == 0:
        pytest.skip(f"No rooms available for {CHECKIN}–{CHECKOUT}")

    # -- Step 2: assign a candidate member to the first room that has them.
    # Only members WITH a membership type qualify: this section exercises the
    # paid wallet path, and members listed as "No Membership - $0" would price
    # at $0 (and currently crash admin add-to-cart — known app bug, see the
    # section 33 findings: cart.py reads membership_type.name without a
    # None-guard).
    chosen_key = None
    sel = selects.first
    options = await sel.locator("option").all()
    for key, _creds in CANDIDATES:
        for opt in options:
            text = (await opt.inner_text()).lower()
            value = await opt.get_attribute("value")
            if value and key in text and "no membership" not in text:
                await sel.select_option(value=value)
                chosen_key = key
                break
        if chosen_key:
            break
    if not chosen_key:
        pytest.skip(
            "Neither Bob nor Alice appears (with a membership type) in the "
            f"room-assignment dropdown for {CHECKIN}–{CHECKOUT}"
        )
    STATE["member_key"] = chosen_key

    # -- Step 3: add to cart ----------------------------------------------
    await pg.click("#room-assignment-form button[type='submit']")
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_2b_after_add_to_cart"))
    # Surface any server-side rejection (permission, conflict, crash) with
    # its actual message instead of failing obscurely later.
    alerts = [
        a.strip() for a in await pg.locator(".alert").all_inner_texts() if a.strip()
    ]
    errors = [a for a in alerts if "error" in a.lower() or "don't have" in a.lower()]
    assert not errors, f"Add-to-cart was rejected by the server: {errors}"

    await pg.goto(ADMIN_CART_URL)
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_2c_cart"))
    # An empty cart redirects back to check-availability — staying on the
    # cart URL is the real signal that the item was added.
    assert "booking-cart" in pg.url, (
        f"Cart is empty after add-to-cart (redirected to {pg.url})"
    )
    cart_content = (await pg.content()).lower()
    assert chosen_key in cart_content, (
        f"Cart page does not show {chosen_key}'s booking after add-to-cart"
    )

    # -- Step 4: checkout — read the total --------------------------------
    await pg.goto(ADMIN_CHECKOUT_URL)
    await pg.wait_for_load_state("networkidle")
    total_text = await pg.locator("#total-amount").first.inner_text()
    total = float(total_text.replace(",", "").replace("$", "").strip())
    assert total > 0, f"Checkout total should be positive, got {total_text!r}"
    STATE["total"] = total

    # -- Step 5: wallet payment -------------------------------------------
    await pg.check("#payment-wallet")
    await pg.wait_for_selector("#wallet-payment-section", state="visible", timeout=5000)

    wallet_cards = pg.locator("#wallet-payment-section .wallet-card")
    if await wallet_cards.count() == 0:
        pytest.skip("No members with wallet funds offered at admin checkout")
    picked = False
    for i in range(await wallet_cards.count()):
        card = wallet_cards.nth(i)
        if chosen_key in (await card.inner_text()).lower():
            await card.locator("input.wallet-member-radio").check()
            picked = True
            break
    assert picked, f"No wallet card for {chosen_key} in the wallet payment section"

    await pg.wait_for_function(
        "!document.getElementById('submit-button').disabled", timeout=5000
    )
    await pg.screenshot(path=screenshot_path("33_2d_checkout_ready"))
    await pg.click("#submit-button")

    # Wallet path is confirmed server-side; JS redirects straight to success.
    await pg.wait_for_url("**/booking-success/**", timeout=45000)
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_2e_booking_success"))

    booking_id = pg.url.rstrip("/").split("/")[-1]
    assert booking_id, f"Could not extract booking id from success URL {pg.url}"
    STATE["booking_id"] = booking_id


# ---------------------------------------------------------------------------
# 33.3 — Booking is listed as confirmed with a refund button
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_3_booking_listed_with_refund_button(booking_admin_page: Page):
    """The new booking appears on Manage Bookings with a refund button."""
    _require("booking_id", "33_2 did not create a booking")
    pg = booking_admin_page
    await pg.goto(ADMIN_MANAGE_URL)
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_3_manage_bookings"))

    bid = STATE["booking_id"]
    assert bid in await pg.content(), (
        f"Booking {bid} not visible on Manage Bookings (pagination/filter issue?)"
    )
    refund_btn = pg.locator(f".refund-booking-btn[data-booking-id='{bid}']")
    assert await refund_btn.count() > 0, (
        f"Booking {bid} has no refund button — expected a confirmed, "
        "refundable booking"
    )


# ---------------------------------------------------------------------------
# 33.4 — Member's wallet was debited by the booking total
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_4_member_wallet_debited(browser):
    """Member's wallet balance dropped by exactly the booking total."""
    _require("booking_id", "33_2 did not create a booking")
    key = STATE["member_key"]
    start = STATE["start_balances"].get(key)
    if start is None:
        pytest.skip(f"No baseline balance recorded for {key} in 33_1")

    creds = dict(CANDIDATES)[key]
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    try:
        await login(pg, creds["email"], creds["password"])
        balance = await _read_wallet_balance(pg)
        await pg.screenshot(path=screenshot_path("33_4_wallet_after_booking"))
    finally:
        await context.close()

    expected = start - STATE["total"]
    assert abs(balance - expected) < 0.011, (
        f"{key}'s wallet is ${balance:.2f}, expected ${expected:.2f} "
        f"(start ${start:.2f} − booking total ${STATE['total']:.2f})"
    )


# ---------------------------------------------------------------------------
# 33.5 — Admin executes a full refund to wallet
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_5_admin_refunds_booking_to_wallet(booking_admin_page: Page):
    """Admin refunds the full amount to the member's wallet via the modal.
    Exercises the confirm() dialog and the async wallet-dropdown load."""
    _require("booking_id", "33_2 did not create a booking")
    pg = booking_admin_page
    bid = STATE["booking_id"]

    await pg.goto(ADMIN_MANAGE_URL)
    await pg.wait_for_load_state("networkidle")

    refund_btn = pg.locator(f".refund-booking-btn[data-booking-id='{bid}']")
    if await refund_btn.count() == 0:
        pytest.skip(f"No refund button for booking {bid} — already refunded?")

    await refund_btn.click()
    await pg.wait_for_selector("#refundBookingModal.show", timeout=5000)

    # The wallet dropdown is populated by an async fetch of
    # api/booking-wallets/<id>/ — wait for a selectable option to appear.
    await pg.wait_for_function(
        "document.querySelectorAll(\"#refund-wallet option[value]:not([value=''])\")"
        ".length > 0",
        timeout=10000,
    )
    first_wallet = await pg.evaluate(
        "document.querySelector(\"#refund-wallet option[value]:not([value=''])\").value"
    )
    await pg.select_option("#refund-wallet", value=first_wallet)

    # Destination defaults to wallet; amount is prefilled with the full total;
    # release-rooms defaults to checked (cancels the booking). Add a reason.
    await pg.fill("#refund-reason", "Automated E2E test refund (section 33)")
    await pg.screenshot(path=screenshot_path("33_5a_refund_modal_filled"))

    # The submit handler raises a confirm() dialog — accept it.
    async def _accept_dialog(dialog):
        await dialog.accept()
    pg.on("dialog", _accept_dialog)

    await pg.click("#refundBookingModal button[type='submit']")
    await pg.wait_for_load_state("networkidle")
    await pg.screenshot(path=screenshot_path("33_5b_after_refund"))

    assert "manage-bookings" in pg.url, (
        f"Expected redirect back to Manage Bookings after refund, got {pg.url}"
    )
    content = await pg.content()
    assert "successfully" in content.lower() or "refund" in content.lower(), (
        "No success message shown after processing the refund"
    )
    # A fully refunded booking must not offer another refund.
    assert await pg.locator(
        f".refund-booking-btn[data-booking-id='{bid}']"
    ).count() == 0, f"Booking {bid} still shows a refund button after full refund"
    STATE["refunded"] = True


# ---------------------------------------------------------------------------
# 33.6 — Member's wallet balance is fully restored (net zero)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_33_6_member_wallet_restored(browser):
    """After the full refund, the member's wallet is back to its 33_1 baseline."""
    _require("refunded", "33_5 did not complete the refund")
    key = STATE["member_key"]
    start = STATE["start_balances"].get(key)
    if start is None:
        pytest.skip(f"No baseline balance recorded for {key} in 33_1")

    creds = dict(CANDIDATES)[key]
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    try:
        await login(pg, creds["email"], creds["password"])
        balance = await _read_wallet_balance(pg)
        await pg.screenshot(path=screenshot_path("33_6_wallet_restored"))
    finally:
        await context.close()

    assert abs(balance - start) < 0.011, (
        f"{key}'s wallet is ${balance:.2f} after refund, expected the "
        f"pre-booking baseline ${start:.2f} — refund did not credit back in full"
    )
