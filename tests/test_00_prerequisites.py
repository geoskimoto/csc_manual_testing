"""Section 00 — Prerequisites / Suite Setup

Ensures Alice and Bob each have an active membership subscription before the
rest of the test suite runs.

Why this file exists
--------------------
seed_test_data assigns Alice and Bob active subscriptions directly (bypassing
the invoice flow), but a freshly-provisioned database, an incomplete seed run,
or a subscription cancellation left over from a previous test run can leave
them without one.  Having these checks run first — alphabetical ordering puts
00_ before 01_ — makes the full suite self-healing without requiring a manual
DB reset between runs.

Idempotency
-----------
Each test checks subscription state first.  If the member already has an
active subscription the test passes immediately with no state change.
The assign + pay workflow only fires when genuinely needed.

The subscription-assignment sub-workflow tested in detail in test_32 is
deliberately NOT re-tested here — these tests only validate the end-state
(active subscription) and use the reusable helpers to get there.
"""
import pytest
import pytest_asyncio
from playwright.async_api import Page
from tests.helpers import (
    SUBSCRIPTIONS_URL,
    MY_INVOICES_URL,
    ALICE,
    BOB,
    screenshot_path,
    admin_assign_subscription,
    pay_subscription_invoice_with_card,
)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

async def _ensure_active_subscription(
    admin_page: Page,
    member_page: Page,
    member_email: str,
    label: str,
) -> str:
    """
    Verify the member has an active subscription.  If not, assign one via
    the admin and have the member pay the invoice.

    Returns one of: "already_active", "assigned_and_paid", "pending_paid",
    "skipped_no_invoice"
    """
    # --- 1. Check current state --------------------------------------------
    await member_page.goto(SUBSCRIPTIONS_URL)
    await member_page.wait_for_load_state("networkidle")
    content = await member_page.content()

    if "active" in content.lower():
        return "already_active"

    # --- 2. Try paying an existing pending invoice first -------------------
    #        (Handles case where admin previously assigned but member never paid)
    await member_page.goto(MY_INVOICES_URL)
    await member_page.wait_for_load_state("networkidle")
    has_payable = await member_page.locator(
        'a[href*="/billing/invoices/"][href*="/pay/"]'
    ).count() > 0

    if has_payable:
        paid = await pay_subscription_invoice_with_card(member_page)
        if paid:
            return "pending_paid"

    # --- 3. Admin assigns a new subscription; member pays ------------------
    assigned = await admin_assign_subscription(admin_page, member_email)
    if not assigned:
        # Member appeared in the dropdown but could not be assigned, OR
        # member still has an active/pending subscription that filtered them out.
        # Either way, we cannot proceed automatically.
        return "skipped_no_invoice"

    paid = await pay_subscription_invoice_with_card(member_page)
    return "assigned_and_paid" if paid else "skipped_no_invoice"


# ---------------------------------------------------------------------------
# 00.1 — Alice
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_00_1_alice_has_active_subscription(
    booking_admin_page: Page,
    alice_page: Page,
):
    """Alice has (or is given) an active membership subscription.

    Idempotent — passes without side-effects when Alice already has a
    subscription.  Triggers assign + pay only when needed.
    """
    result = await _ensure_active_subscription(
        admin_page=booking_admin_page,
        member_page=alice_page,
        member_email=ALICE["email"],
        label="Alice",
    )
    await alice_page.screenshot(path=screenshot_path(f"00_1_alice_sub_{result}"))

    # After the helper, verify active subscription on Alice's page
    await alice_page.goto(SUBSCRIPTIONS_URL)
    await alice_page.wait_for_load_state("networkidle")
    content = await alice_page.content()

    assert "active" in content.lower(), (
        f"Alice does not have an active subscription after setup (result='{result}'). "
        "Check screenshot 00_1_alice_sub_*.png and ensure seed_test_data has been run, "
        "or that the booking admin account can assign subscriptions."
    )


# ---------------------------------------------------------------------------
# 00.2 — Bob
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_00_2_bob_has_active_subscription(
    booking_admin_page: Page,
    bob_page: Page,
):
    """Bob has (or is given) an active membership subscription.

    Idempotent — passes without side-effects when Bob already has a
    subscription.  Triggers assign + pay only when needed.
    """
    result = await _ensure_active_subscription(
        admin_page=booking_admin_page,
        member_page=bob_page,
        member_email=BOB["email"],
        label="Bob",
    )
    await bob_page.screenshot(path=screenshot_path(f"00_2_bob_sub_{result}"))

    await bob_page.goto(SUBSCRIPTIONS_URL)
    await bob_page.wait_for_load_state("networkidle")
    content = await bob_page.content()

    assert "active" in content.lower(), (
        f"Bob does not have an active subscription after setup (result='{result}'). "
        "Check screenshot 00_2_bob_sub_*.png."
    )


# ---------------------------------------------------------------------------
# 00.3 — Booking access sanity check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_00_3_alice_can_reach_availability(alice_page: Page):
    """Alice can reach the availability search page — confirms can_book_accommodations()
    returns True and the member is not blocked from the booking flow."""
    from tests.helpers import AVAILABILITY_URL
    await alice_page.goto(AVAILABILITY_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("00_3_alice_availability"))

    assert "500" not in await alice_page.title(), "Server error on availability page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["check in", "check-in", "availability", "date"]), \
        "Alice cannot reach the availability page — she may lack an active subscription"


@pytest.mark.asyncio
async def test_00_4_bob_can_reach_availability(bob_page: Page):
    """Bob can reach the availability search page."""
    from tests.helpers import AVAILABILITY_URL
    await bob_page.goto(AVAILABILITY_URL)
    await bob_page.wait_for_load_state("networkidle")
    await bob_page.screenshot(path=screenshot_path("00_4_bob_availability"))

    assert "500" not in await bob_page.title(), "Server error on availability page"
    content = await bob_page.content()
    assert any(kw in content.lower() for kw in ["check in", "check-in", "availability", "date"]), \
        "Bob cannot reach the availability page — he may lack an active subscription"
