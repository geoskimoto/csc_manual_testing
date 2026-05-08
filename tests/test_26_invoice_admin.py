"""Section 26 — Invoice Admin: Dashboard, Create, Send, Record Payment, Void

Accessible to both Booking Admins and Financial Admins (BookingAdminRequiredMixin).
Tests cover access control, dashboard structure, and the full create → send →
record payment and create → void workflows.
"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import BILLING_ADMIN_URL, BILLING_CREATE_URL, screenshot_path

DUE_DATE = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")


async def _create_draft_invoice(page: Page, title: str) -> str:
    """Helper: fill and submit the create invoice wizard. Returns the resulting page URL."""
    await page.goto(BILLING_CREATE_URL)
    await page.wait_for_load_state("networkidle")

    # Select first available customer (index 0 is blank placeholder)
    await page.select_option('select[name="customer"]', index=1)
    await page.fill('input[name="title"]', title)
    await page.fill('input[name="due_date"]', DUE_DATE)

    # Limit formset to 1 row so empty extra rows don't trip validation
    await page.evaluate("document.querySelector('input[name=\"form-TOTAL_FORMS\"]').value = '1'")
    await page.fill('input[name="form-0-description"]', "Playwright test item")
    await page.fill('input[name="form-0-quantity"]', "1")
    await page.fill('input[name="form-0-unit_price"]', "25.00")

    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    return page.url


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_26_1_dashboard_loads_for_financial_admin(financial_admin_page: Page):
    """Invoice admin dashboard loads for Financial Admin (200)."""
    response = await financial_admin_page.goto(BILLING_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_1_fa_billing_dashboard"))
    assert response.status == 200
    content = await financial_admin_page.content()
    assert "invoice" in content.lower()


@pytest.mark.asyncio
async def test_26_2_dashboard_loads_for_booking_admin(booking_admin_page: Page):
    """Invoice admin dashboard loads for Booking Admin (200)."""
    response = await booking_admin_page.goto(BILLING_ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("26_2_ba_billing_dashboard"))
    assert response.status == 200


@pytest.mark.asyncio
async def test_26_3_member_cannot_access(alice_page: Page):
    """Regular member is redirected away from invoice admin dashboard."""
    await alice_page.goto(BILLING_ADMIN_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("26_3_member_blocked"))
    assert BILLING_ADMIN_URL.split("3rdplaces.io")[1] not in alice_page.url \
        or "/sign-in" in alice_page.url or "/dashboard" in alice_page.url


# ---------------------------------------------------------------------------
# Dashboard structure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_26_4_dashboard_shows_statistics_and_list(financial_admin_page: Page):
    """Dashboard shows dollar-amount stats and an invoice list table."""
    await financial_admin_page.goto(BILLING_ADMIN_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("26_4_billing_stats"))
    assert "$" in content, "No dollar amounts on dashboard"
    # Invoice list table headers
    assert "Invoice" in content and "Customer" in content


@pytest.mark.asyncio
async def test_26_5_create_page_loads_with_form_fields(financial_admin_page: Page):
    """Create invoice page loads and shows customer, title, due date and line items."""
    await financial_admin_page.goto(BILLING_CREATE_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    content = await financial_admin_page.content()
    await financial_admin_page.screenshot(path=screenshot_path("26_5_create_invoice_form"))
    assert "customer" in content.lower() or "Customer" in content
    assert "title" in content.lower() or "Title" in content
    assert "due_date" in content or "Due Date" in content
    assert "description" in content.lower()


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_26_6_create_draft_invoice(financial_admin_page: Page):
    """Create a draft invoice: fills form, submits, lands on invoice detail page."""
    url = await _create_draft_invoice(financial_admin_page, "Playwright Draft Invoice")
    await financial_admin_page.screenshot(path=screenshot_path("26_6_created_invoice"))
    # Should land on the invoice detail page after creation
    assert "admin-tool" in url, f"Unexpected URL after create: {url}"
    content = await financial_admin_page.content()
    assert "Draft" in content or "Playwright Draft Invoice" in content, \
        "Invoice detail page did not show after creation"


@pytest.mark.asyncio
async def test_26_7_send_invoice(financial_admin_page: Page):
    """Create a draft invoice then send it; invoice status changes to Sent."""
    await _create_draft_invoice(financial_admin_page, "Playwright Send Test Invoice")
    # We're now on the invoice detail page — find the Send link
    send_link = financial_admin_page.locator("a", has_text="Send").first
    await send_link.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_7_send_invoice_page"))
    content = await financial_admin_page.content()
    # Send page should show invoice info and a submit button
    assert "Send" in content or "Email" in content
    # Submit the send form
    await financial_admin_page.click('button[type="submit"]')
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_7b_sent_invoice"))
    content = await financial_admin_page.content()
    assert "Sent" in content or "sent" in content, \
        "Invoice status did not change to Sent after sending"


@pytest.mark.asyncio
async def test_26_8_record_payment(financial_admin_page: Page):
    """Create and send an invoice then record a manual payment; invoice becomes Paid."""
    url = await _create_draft_invoice(financial_admin_page, "Playwright Payment Test Invoice")
    # Send it first
    send_link = financial_admin_page.locator("a", has_text="Send").first
    await send_link.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.click('button[type="submit"]')
    await financial_admin_page.wait_for_load_state("networkidle")

    # Now record a payment
    payment_link = financial_admin_page.locator("a", has_text="Record Payment").first
    await payment_link.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_8_record_payment_form"))
    # Fill payment form
    await financial_admin_page.fill('input[name="amount"]', "25.00")
    await financial_admin_page.select_option('select[name="payment_method"]', value="manual")
    await financial_admin_page.click('button[type="submit"]')
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_8b_paid_invoice"))
    content = await financial_admin_page.content()
    assert "Paid" in content or "paid" in content, \
        "Invoice did not transition to Paid after recording full payment"


@pytest.mark.asyncio
async def test_26_9_void_draft_invoice(financial_admin_page: Page):
    """Create a draft invoice then void it; invoice status changes to Void."""
    await _create_draft_invoice(financial_admin_page, "Playwright Void Test Invoice")
    # Find the Void link on the detail page
    void_link = financial_admin_page.locator("a", has_text="Void").first
    await void_link.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_9_void_invoice_page"))
    content = await financial_admin_page.content()
    assert "Void" in content or "void" in content
    # Fill void form
    await financial_admin_page.fill('textarea[name="reason"]', "Playwright automated test - safe to void")
    await financial_admin_page.check('input[name="confirm"]')
    await financial_admin_page.click('button[type="submit"]')
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("26_9b_voided_invoice"))
    content = await financial_admin_page.content()
    assert "Void" in content, "Invoice did not show Void status after voiding"
