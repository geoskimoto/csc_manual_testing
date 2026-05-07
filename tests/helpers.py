from pathlib import Path
from playwright.async_api import Page

BASE_URL = "https://csc-booking-test.3rdplaces.io"
ALICE           = {"email": "alice.tester@csc-test.local",    "password": "TestPass99!"}
BOB             = {"email": "bob.tester@csc-test.local",      "password": "TestPass99!"}
BOOKING_ADMIN   = {"email": "booking.admin@csc-test.local",   "password": "AdminPass99!"}
FINANCIAL_ADMIN = {"email": "financial.admin@csc-test.local", "password": "AdminPass99!"}
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
