from pathlib import Path
from playwright.async_api import Page

BASE_URL = "https://csc-booking-test.3rdplaces.io"
ALICE           = {"email": "alice.tester@csc-test.local",    "password": "TestPass99!"}
BOB             = {"email": "bob.tester@csc-test.local",      "password": "TestPass99!"}
BOOKING_ADMIN   = {"email": "booking.admin@csc-test.local",   "password": "AdminPass99!"}
FINANCIAL_ADMIN = {"email": "financial.admin@csc-test.local", "password": "AdminPass99!"}
MEMBERS_PLUS    = {"email": "members.plus@csc-test.local",    "password": "AdminPass99!"}
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"

# Member-facing URLs
LOGIN_URL         = f"{BASE_URL}/user/sign-in/"
SIGN_UP_URL       = f"{BASE_URL}/user/sign-up/"
MEMBERSHIP_APP_URL= f"{BASE_URL}/user/membership_application/"
DASHBOARD_URL     = f"{BASE_URL}/dashboard/"
PROFILE_URL       = f"{BASE_URL}/dashboard/profile/"
WALLET_URL        = f"{BASE_URL}/dashboard/wallet/"
AVAILABILITY_URL  = f"{BASE_URL}/bookings/check_availability/"
CART_URL          = f"{BASE_URL}/bookings/view_booking_cart/"
ADD_TO_CART_URL   = f"{BASE_URL}/bookings/add_accommodations_to_cart/"
REMOVE_CART_URL   = f"{BASE_URL}/bookings/remove-cart-item/"
CLEAR_CART_URL    = f"{BASE_URL}/bookings/clear-cart/"
CHECKOUT_URL      = f"{BASE_URL}/bookings/checkout/"
NOTIFICATIONS_URL = f"{BASE_URL}/notifications/"
MY_INVOICES_URL   = f"{BASE_URL}/billing/my-invoices/"
SUBSCRIPTIONS_URL = f"{BASE_URL}/subscriptions/"

# Admin URLs
ADMIN_URL             = f"{BASE_URL}/admin-bookings/"
ADMIN_MANAGE_URL      = f"{BASE_URL}/admin-bookings/manage-bookings/"
ADMIN_AVAIL_URL       = f"{BASE_URL}/admin-bookings/check-availability/"
ADMIN_CART_URL        = f"{BASE_URL}/admin-bookings/booking-cart/"
ADMIN_CHECKOUT_URL    = f"{BASE_URL}/admin-bookings/checkout/"
ADMIN_TXNS_URL        = f"{BASE_URL}/admin-bookings/transactions/"
ADMIN_SEARCH_URL      = f"{BASE_URL}/admin-bookings/search-members/"
BILLING_ADMIN_URL     = f"{BASE_URL}/billing/admin-tool/"
BILLING_CREATE_URL    = f"{BASE_URL}/billing/admin-tool/create/"
SUBS_ADMIN_URL        = f"{BASE_URL}/subscriptions/admin/list/"
SUBS_ADMIN_ASSIGN_URL = f"{BASE_URL}/subscriptions/admin/assign/"
STUCK_PAYMENTS_URL    = f"{BASE_URL}/bookings/admin/stuck-payment-dashboard/"

# Newer feature URLs
BED_LIST_URL  = f"{BASE_URL}/dashboard/bed-list-calendar/"
EVENTS_URL    = f"{BASE_URL}/events/"

# Newsletters (Members+ capability)
NEWSLETTERS_URL        = f"{BASE_URL}/newsletters/"
NEWSLETTERS_MANAGE_URL = f"{BASE_URL}/newsletters/manage/"

# Admin alert recipients
ADMIN_ALERT_RECIPIENTS_URL = f"{BASE_URL}/notifications/admin/alert-recipients/"

# Financial dashboard / reporting
FINANCIAL_DASHBOARD_URL   = f"{BASE_URL}/financials/"
DEFERRED_REVENUE_URL      = f"{BASE_URL}/financials/deferred-revenue/"
AR_AGING_URL              = f"{BASE_URL}/financials/ar-aging/"

# Credit Member Wallet (admin)
CREDIT_WALLET_URL = f"{BASE_URL}/admin-bookings/credit-wallet/"

# Promote-to-Account-Holder (admin picker + public token acceptance)
PROMOTE_PROFILE_URL       = f"{BASE_URL}/user/admin/promote-profile/"
PROMOTE_ACCEPT_URL_STEM   = f"{BASE_URL}/user/promote/"  # + <token>/

# Waivers app. There is no fixed GUEST_SIGN_URL constant — the seeded
# WaiverTemplate defaults to audience='members' and 404s from the public
# guest-sign route by design, so tests discover a live guest-facing
# template's path dynamically (see test_39_waivers.py::_discover_guest_sign_path).
MY_WAIVERS_URL          = f"{BASE_URL}/waivers/"
WAIVER_SIGN_REQUIRED_URL = f"{BASE_URL}/waivers/sign-required/"
WAIVER_COMPLIANCE_URL    = f"{BASE_URL}/waivers/manage/"
WAIVER_GUEST_LIST_URL    = f"{BASE_URL}/waivers/manage/guests/"
WAIVER_GUEST_LINKS_URL   = f"{BASE_URL}/waivers/manage/guest-links/"

# Broadcasts app (admin club-wide email)
BROADCASTS_URL         = f"{BASE_URL}/broadcasts/"
BROADCASTS_COMPOSE_URL = f"{BASE_URL}/broadcasts/new/"

# Maintenance Reports (Members+ / Booking Admin) — lodge.urls is mounted at
# the site root, not under /lodge/.
MAINTENANCE_REPORTS_URL = f"{BASE_URL}/maintenance-reports/"

# Profile Integrity admin detail page (Financial Admin only)
PROFILE_INTEGRITY_URL = f"{BASE_URL}/user/admin/profile-integrity/"


def screenshot_path(name: str) -> str:
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    return str(SCREENSHOT_DIR / f"{name}.png")


async def login(page: Page, email: str, password: str):
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="email"]', email)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")


async def fill_ckeditor(page: Page, field_id: str, text: str):
    """Set a django-ckeditor-5 field's content via its JS API.

    CKEditor5 replaces the source <textarea> with a contenteditable rich-text
    area and only syncs back to the textarea on form submit — clicking/typing
    into the rich-text area is brittle across versions and layouts.
    django-ckeditor-5 exposes the live editor instance as
    `<textarea>.ckeditorInstance`, so setting data through that is the
    reliable path. Falls back to a plain value set if the editor hasn't
    initialized (e.g. its JS bundle is still loading).
    """
    await page.evaluate(
        """([id, text]) => {
            const el = document.getElementById(id);
            if (el && el.ckeditorInstance) {
                el.ckeditorInstance.setData(text);
            } else if (el) {
                el.value = text;
            }
        }""",
        [field_id, text],
    )


async def switch_to_card_view(page: Page):
    """Switch the member-facing availability page from Map View to Card View.

    Since commit 6b0b351, Map View is the default on this page and #rooms-content
    (card view, where select.member-select occupant dropdowns live) starts hidden
    behind the Card/Map toggle. Call this after searching availability and before
    interacting with select.member-select. No-op if the toggle isn't present
    (e.g. the admin availability page uses a different template).
    """
    toggle = page.locator("#view-toggle-card")
    if await toggle.count() == 0:
        return
    await toggle.click()
    try:
        await page.wait_for_selector("#rooms-content", state="visible", timeout=10000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Reusable subscription-assignment helpers
# ---------------------------------------------------------------------------

async def admin_assign_subscription(admin_page: Page, member_email: str) -> bool:
    """Admin assigns a new subscription to a member via the admin assign page.

    Returns True on success, False if the member already has an active/pending
    subscription (they won't appear in the Select2 dropdown).

    Usage example (from another test):
        from tests.helpers import admin_assign_subscription
        ok = await admin_assign_subscription(booking_admin_page, BOB["email"])
        assert ok, "Bob should have been assignable (no active subscription)"
    """
    await admin_page.goto(SUBS_ADMIN_ASSIGN_URL)
    await admin_page.wait_for_load_state("networkidle")

    # -- Select the member profile via the underlying <select> element --------
    # Using select_option() directly is more reliable than clicking the Select2
    # UI, which depends on the CDN-loaded Select2 library initialising.
    # Select2 listens for changes on the underlying <select> so both approaches
    # end up dispatching the same change event.
    profile_select = admin_page.locator("#profile_id")
    options = await profile_select.locator("option").all()
    chosen_value = None
    for opt in options:
        val = await opt.get_attribute("value")
        text = await opt.inner_text()
        if val and member_email.split("@")[0].lower() in text.lower():
            chosen_value = val
            break
    if chosen_value is None:
        # No matching option — member already has an active subscription
        return False

    await profile_select.select_option(value=chosen_value)
    await admin_page.wait_for_timeout(300)

    # -- Select first available membership type --------------------------------
    membership_select = admin_page.locator("#membership_type_id")
    options = await membership_select.locator("option").all()
    for opt in options:
        val = await opt.get_attribute("value")
        if val:
            await membership_select.select_option(value=val)
            break
    await admin_page.wait_for_timeout(500)

    # -- Submit ----------------------------------------------------------------
    await admin_page.locator("button[type='submit']").click()
    await admin_page.wait_for_load_state("networkidle")

    # Success = redirected back to the admin subscription list
    return "subscriptions/admin" in admin_page.url


async def pay_subscription_invoice_with_card(
    member_page: Page,
    card_number: str = "4242424242424242",
) -> bool:
    """Member pays their most recent unpaid invoice using a Stripe test card.

    Navigates to MY_INVOICES_URL, clicks the first available "Pay" link, fills
    in the Stripe PaymentElement, and waits for the payment-success redirect.

    Returns True on success, False if no payable invoice was found or the
    Stripe element could not be interacted with.

    Usage example (from another test):
        from tests.helpers import pay_subscription_invoice_with_card
        ok = await pay_subscription_invoice_with_card(bob_page)
        assert ok, "Invoice payment should have succeeded"
    """
    await member_page.goto(MY_INVOICES_URL)
    await member_page.wait_for_load_state("networkidle")

    # Find a Pay Now link for an unpaid invoice
    pay_link = member_page.locator('a.btn-success[href*="/billing/invoices/"][href*="/pay/"]').first
    if await pay_link.count() == 0:
        return False

    await pay_link.click()
    # "load" not "networkidle" — the invoice payment page mounts Stripe's
    # PaymentElement, which keeps network activity alive (same reason the
    # checkout Stripe tests avoid networkidle) and would time this out.
    await member_page.wait_for_load_state("load")
    # Give Stripe time to mount the PaymentElement
    await member_page.wait_for_timeout(4000)

    # -- Fill in Stripe PaymentElement ----------------------------------------
    # PaymentElement mounts as an <iframe> inside #payment-element.
    # The element uses tab layout restricted to card only.
    try:
        await member_page.wait_for_selector("#payment-element iframe", timeout=15000)
        pf = member_page.frame_locator("#payment-element iframe").first

        # Card number — try autocomplete attr first, fall back to placeholder
        card_el = pf.locator('input[autocomplete="cc-number"]')
        if await card_el.count() == 0:
            card_el = pf.locator('input[placeholder*="1234"]')
        await card_el.fill(card_number)
        await member_page.wait_for_timeout(300)

        exp_el = pf.locator('input[autocomplete="cc-exp"]')
        if await exp_el.count() == 0:
            exp_el = pf.locator('input[placeholder*="MM"]')
        await exp_el.fill("1234")
        await member_page.wait_for_timeout(300)

        cvc_el = pf.locator('input[autocomplete="cc-csc"]')
        if await cvc_el.count() == 0:
            cvc_el = pf.locator('input[placeholder*="CVC"]')
        await cvc_el.fill("123")
        await member_page.wait_for_timeout(300)

    except Exception:
        return False

    # -- Submit and wait for success redirect ----------------------------------
    await member_page.locator("#pay-button").click()
    try:
        await member_page.wait_for_url("**/billing/invoices/**", timeout=30000)
    except Exception:
        pass  # Already on success page or URL pattern differs

    final_url = member_page.url
    return "payment=success" in final_url or "paid" in final_url or "invoices" in final_url
