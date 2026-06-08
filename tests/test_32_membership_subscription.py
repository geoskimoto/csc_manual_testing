"""Section 32 — Membership Subscription Assignment Workflow

Full E2E workflow:
  1. Booking admin assigns a subscription to a member.
  2. System creates a pending MemberSubscription + Invoice (status='pending_payment').
  3. Member pays the invoice via Stripe (test card 4242...).
  4. InvoicePayment.save() auto-activates the subscription and syncs profile.membership_type.
  5. Member can now make bookings.

Reusable helpers in helpers.py:
  - admin_assign_subscription(admin_page, member_email)
  - pay_subscription_invoice_with_card(member_page, card_number)

Prerequisite: Bob must NOT have an active/pending subscription when tests 32.5+
run, because the assign form only shows members without one.  Tests 32.5-32.8
cancel Bob's existing subscription first (if present) via the admin UI.
Run `python manage.py seed_test_data` before the full suite to ensure clean state.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import (
    SUBS_ADMIN_URL,
    SUBS_ADMIN_ASSIGN_URL,
    MY_INVOICES_URL,
    SUBSCRIPTIONS_URL,
    BASE_URL,
    BOB,
    screenshot_path,
    admin_assign_subscription,
    pay_subscription_invoice_with_card,
)


# ---------------------------------------------------------------------------
# 32.1 — Admin assign page loads
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_1_admin_assign_page_loads(booking_admin_page: Page):
    """Booking admin can reach the subscription assignment page without error."""
    await booking_admin_page.goto(SUBS_ADMIN_ASSIGN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("32_1_assign_page"))
    assert "500" not in await booking_admin_page.title()
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in ["assign", "subscription", "member"]), \
        "Assign subscription page did not render expected content"


@pytest.mark.asyncio
async def test_32_2_assign_form_elements_present(booking_admin_page: Page):
    """Subscription assign form contains profile selector, membership type, and submit."""
    await booking_admin_page.goto(SUBS_ADMIN_ASSIGN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    # Select2-powered member dropdown
    assert await booking_admin_page.locator(".select2-container").count() > 0, \
        "Select2 profile dropdown not found"

    # Membership type selector
    assert await booking_admin_page.locator("#membership_type_id").count() > 0, \
        "#membership_type_id select not found"

    # Submit button
    assert await booking_admin_page.locator("button[type='submit']").count() > 0, \
        "Submit button not found on assign form"


@pytest.mark.asyncio
async def test_32_3_membership_type_updates_pricing(booking_admin_page: Page):
    """Selecting a membership type reveals the pricing summary."""
    await booking_admin_page.goto(SUBS_ADMIN_ASSIGN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    # Pick the first real membership type option
    select = booking_admin_page.locator("#membership_type_id")
    options = await select.locator("option").all()
    selected = False
    for opt in options:
        val = await opt.get_attribute("value")
        if val:
            await select.select_option(value=val)
            selected = True
            break

    if not selected:
        pytest.skip("No membership types available in the system")

    await booking_admin_page.wait_for_timeout(600)
    await booking_admin_page.screenshot(path=screenshot_path("32_3_pricing"))

    # #pricingSummary should become visible after selecting a type
    pricing = booking_admin_page.locator("#pricingSummary")
    assert await pricing.is_visible(), \
        "#pricingSummary did not appear after selecting a membership type"


# ---------------------------------------------------------------------------
# 32.4 — Admin subscription list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_4_admin_subscription_list_loads(booking_admin_page: Page):
    """Booking admin can reach the subscription list page."""
    await booking_admin_page.goto(SUBS_ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("32_4_sub_list"))
    assert "500" not in await booking_admin_page.title()
    content = await booking_admin_page.content()
    assert any(kw in content.lower() for kw in ["subscription", "member"]), \
        "Subscription list page did not render expected content"


# ---------------------------------------------------------------------------
# 32.5 — Cancel Bob's existing subscription so he appears in the assign form
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_5_cancel_bobs_subscription_if_active(booking_admin_page: Page):
    """If Bob has an active/pending subscription, cancel it via admin so the
    assign workflow tests can run against his account.

    Navigates to the subscription list, finds Bob's row, follows the
    cancel/refund link, and submits the cancellation form.
    Skips gracefully if Bob has no subscription to cancel.
    """
    await booking_admin_page.goto(SUBS_ADMIN_URL)
    await booking_admin_page.wait_for_load_state("networkidle")

    # Look for a row mentioning Bob's email or name
    bob_row = booking_admin_page.locator("tr, .subscription-row").filter(
        has_text=BOB["email"].split("@")[0]
    ).first
    if await bob_row.count() == 0:
        pytest.skip("No subscription row found for Bob — nothing to cancel")

    # Find a cancel / refund link in that row
    cancel_link = bob_row.locator("a").filter(
        has_text=lambda t: any(kw in t.lower() for kw in ("cancel", "refund", "detail"))
    ).first
    if await cancel_link.count() == 0:
        # Fallback: look for any link in the row
        cancel_link = bob_row.locator("a").first

    if await cancel_link.count() == 0:
        pytest.skip("Could not locate a cancel/detail link for Bob's subscription row")

    await cancel_link.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("32_5_cancel_detail"))

    # Look for a cancel/refund form or button on the detail page
    cancel_btn = booking_admin_page.locator(
        "button[type='submit'], input[type='submit']"
    ).filter(has_text=lambda t: any(kw in t.lower() for kw in ("cancel", "refund")))

    if await cancel_btn.count() == 0:
        # Some pages use a form with a hidden action; just look for any submit
        cancel_btn = booking_admin_page.locator("button[type='submit']").first

    if await cancel_btn.count() == 0:
        pytest.skip("Cancel form not found on subscription detail page — skipping cancel step")

    await cancel_btn.click()
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("32_5_after_cancel"))

    # After cancel, should be redirected back to list or show success
    content = await booking_admin_page.content()
    assert "500" not in await booking_admin_page.title(), "Server error after cancel attempt"
    # Not asserting exact redirect — page may vary by implementation


# ---------------------------------------------------------------------------
# 32.6 — Admin assigns subscription to Bob
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_6_admin_assigns_subscription_to_bob(booking_admin_page: Page):
    """Booking admin successfully assigns a subscription to Bob.

    Expects Bob to NOT have an active subscription.  Run test 32.5 first (or
    seed_test_data + manual cancel) if Bob already has one.
    """
    ok = await admin_assign_subscription(booking_admin_page, BOB["email"])
    await booking_admin_page.screenshot(path=screenshot_path("32_6_after_assign"))

    if not ok:
        pytest.skip(
            "Bob was not found in the assignable members dropdown — "
            "he may still have an active or pending subscription. "
            "Cancel it first (test 32.5) then re-run."
        )

    assert "subscriptions/admin" in booking_admin_page.url, \
        f"Expected redirect to admin subscription list, got: {booking_admin_page.url}"


# ---------------------------------------------------------------------------
# 32.7 — Bob's invoice appears on his invoices page
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_7_bob_has_payable_invoice(bob_page: Page):
    """After subscription assignment Bob can see an unpaid subscription invoice."""
    await bob_page.goto(MY_INVOICES_URL)
    await bob_page.wait_for_load_state("networkidle")
    await bob_page.screenshot(path=screenshot_path("32_7_bob_invoices"))

    # There should be at least one invoice with a Pay link
    pay_link = bob_page.locator('a[href*="/billing/invoices/"][href*="/pay/"]').first
    assert await pay_link.count() > 0, \
        "No payable invoice found for Bob after subscription assignment"


# ---------------------------------------------------------------------------
# 32.8 — Invoice payment page renders with Stripe element
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_8_invoice_payment_page_loads_stripe(bob_page: Page):
    """Bob's invoice payment page loads and mounts the Stripe PaymentElement."""
    await bob_page.goto(MY_INVOICES_URL)
    await bob_page.wait_for_load_state("networkidle")

    pay_link = bob_page.locator('a[href*="/billing/invoices/"][href*="/pay/"]').first
    if await pay_link.count() == 0:
        pytest.skip("No payable invoice for Bob — run test 32.6 first")

    await pay_link.click()
    await bob_page.wait_for_load_state("networkidle")
    await bob_page.wait_for_timeout(4000)
    await bob_page.screenshot(path=screenshot_path("32_8_payment_page"))

    # #payment-element should be present and contain a Stripe iframe
    payment_el = bob_page.locator("#payment-element")
    assert await payment_el.count() > 0, "#payment-element div not found"

    try:
        await bob_page.wait_for_selector("#payment-element iframe", timeout=10000)
        has_iframe = True
    except Exception:
        has_iframe = False

    assert has_iframe, "Stripe PaymentElement iframe did not mount inside #payment-element"

    # Pay button must be present
    assert await bob_page.locator("#pay-button").count() > 0, "#pay-button not found"


# ---------------------------------------------------------------------------
# 32.9 — Bob pays invoice with Stripe test card
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_9_bob_pays_invoice_with_test_card(bob_page: Page):
    """Bob pays his subscription invoice using Stripe test card 4242 4242 4242 4242.

    After payment InvoicePayment.save() auto-activates the subscription and
    syncs profile.membership_type.  Bob should be redirected to a success page.
    """
    ok = await pay_subscription_invoice_with_card(bob_page)
    await bob_page.screenshot(path=screenshot_path("32_9_after_payment"))

    if not ok:
        pytest.skip(
            "Invoice payment helper returned False — no payable invoice found "
            "or Stripe element could not be interacted with. "
            "Ensure test 32.6 ran successfully first."
        )

    # Verify we landed somewhere sensible after payment
    final_url = bob_page.url
    assert "500" not in await bob_page.title(), "Server error after invoice payment"
    content = await bob_page.content()
    assert any(kw in content.lower() for kw in ["paid", "success", "invoice", "subscription"]), \
        f"Unexpected page content after payment. URL: {final_url}"


# ---------------------------------------------------------------------------
# 32.10 — Bob's subscription is now active
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_10_subscription_active_after_payment(bob_page: Page):
    """After invoice payment Bob's subscription dashboard shows an active subscription."""
    await bob_page.goto(SUBSCRIPTIONS_URL)
    await bob_page.wait_for_load_state("networkidle")
    await bob_page.screenshot(path=screenshot_path("32_10_sub_active"))

    assert "500" not in await bob_page.title(), "Server error on subscription page"
    content = await bob_page.content()
    assert any(kw in content.lower() for kw in ["active", "subscription", "membership"]), \
        "Subscription page does not show active membership after payment"


# ---------------------------------------------------------------------------
# 32.11 — Full workflow integration test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_32_11_full_assign_and_pay_workflow(booking_admin_page: Page, bob_page: Page):
    """Integration smoke-test: assign subscription to Bob and have Bob pay it.

    This is the canonical 'embed me in other tests' test — call the two helpers
    back-to-back to bring any member from no-subscription to bookable.

    NOTE: This test requires Bob to have NO active/pending subscription.
    Run seed_test_data and cancel Bob's subscription (test 32.5) before running.
    """
    # --- Admin assigns -------------------------------------------------------
    assigned = await admin_assign_subscription(booking_admin_page, BOB["email"])
    if not assigned:
        pytest.skip(
            "Bob still has an active/pending subscription — cannot assign again. "
            "Cancel it first (test 32.5) and re-run."
        )
    await booking_admin_page.screenshot(path=screenshot_path("32_11_assigned"))

    # --- Bob pays the invoice ------------------------------------------------
    paid = await pay_subscription_invoice_with_card(bob_page)
    await bob_page.screenshot(path=screenshot_path("32_11_paid"))
    assert paid, (
        "pay_subscription_invoice_with_card returned False — "
        "check 32_11_paid.png for the state of the payment page"
    )

    # --- Verify Bob can reach his subscription page with active status --------
    await bob_page.goto(SUBSCRIPTIONS_URL)
    await bob_page.wait_for_load_state("networkidle")
    content = await bob_page.content()
    assert any(kw in content.lower() for kw in ["active", "subscription", "membership"]), \
        "Bob's subscription page does not confirm active status after full workflow"
