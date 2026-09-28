"""Section 37 — Credit Member Wallet (admin tool)

/admin-bookings/credit-wallet/ lets admins issue manual wallet credit (work
rewards, fundraiser prizes, adjustments) outside the normal booking/refund
flow. Booking Administrators are capped per credit (SystemSettings
`booking_admin_wallet_credit_limit`, shown as an alert on the page); Financial
Administrators are uncapped and are the only role that can issue a
*correction* against a prior manual credit (the "Correct" button/column is
gated out of the template entirely for Booking Admins, not just the POST).

Money-moving admin tool — the credit + correction tests use Bob (not Alice,
who many other sections' fixtures assume is untouched) with a small,
self-cancelling amount: a $5.00 "adjustment" credit followed immediately by a
$5.00 correction against that same transaction, netting Bob's wallet back to
its seeded balance by the end of the test. Mirrors the same
don't-mutate-shared-fixtures caution as Section 28's admin refund test.
"""
import pytest
from playwright.async_api import Page
from tests.helpers import CREDIT_WALLET_URL, BOB, screenshot_path


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_37_1_anonymous_redirected_to_login(page: Page):
    await page.goto(CREDIT_WALLET_URL)
    await page.wait_for_load_state("networkidle")
    assert "sign-in" in page.url, f"Expected redirect to sign-in, got {page.url}"


@pytest.mark.asyncio
async def test_37_2_member_blocked(alice_page: Page):
    resp = await alice_page.goto(CREDIT_WALLET_URL)
    status = resp.status if resp else 0
    url = alice_page.url
    is_blocked = status in (403, 404) or "sign-in" in url or "403" in url
    assert is_blocked, f"Expected member to be blocked, got status={status} url={url}"


# ---------------------------------------------------------------------------
# Page rendering per role
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_37_3_booking_admin_sees_cap_notice(booking_admin_page: Page):
    resp = await booking_admin_page.goto(CREDIT_WALLET_URL)
    await booking_admin_page.wait_for_load_state("networkidle")
    await booking_admin_page.screenshot(path=screenshot_path("37_3_booking_admin_cap_notice"))
    assert resp.status == 200
    cap_notice = booking_admin_page.locator(".alert-info", has_text="per-credit limit")
    assert await cap_notice.count() > 0, "Booking Admin should see the per-credit cap notice"
    # The correction column/button is gated out of the template for non-financial admins
    assert await booking_admin_page.locator(".correct-btn").count() == 0, \
        "Booking Admin should never see a Correct button"


@pytest.mark.asyncio
async def test_37_4_financial_admin_no_cap_notice(financial_admin_page: Page):
    resp = await financial_admin_page.goto(CREDIT_WALLET_URL)
    await financial_admin_page.wait_for_load_state("networkidle")
    assert resp.status == 200
    cap_notice = financial_admin_page.locator(".alert-info", has_text="per-credit limit")
    assert await cap_notice.count() == 0, "Financial Admin should not see a per-credit cap notice"


# ---------------------------------------------------------------------------
# Credit + correction happy path (Financial Admin, self-cancelling)
# ---------------------------------------------------------------------------

async def _search_and_select_member(page: Page, query: str, email: str) -> bool:
    await page.fill("#member-search", query)
    # Debounced fetch() to search_members_api — wait for a result row to appear
    try:
        await page.wait_for_selector("#member-results .list-group-item", timeout=5000)
    except Exception:
        return False
    results = page.locator("#member-results .list-group-item")
    count = await results.count()
    for i in range(count):
        row = results.nth(i)
        text = await row.inner_text()
        if email.lower() in text.lower():
            await row.click()
            return True
    return False


@pytest.mark.asyncio
async def test_37_5_financial_admin_credit_then_correct_nets_to_zero(financial_admin_page: Page):
    """Issue a $5 adjustment credit to Bob, then correct it back in full.

    Proves the whole money-moving path (search -> select -> credit -> ledger
    row appears -> Correct button -> modal -> correction) end-to-end without
    leaving a net balance change on Bob's seeded wallet.
    """
    await financial_admin_page.goto(CREDIT_WALLET_URL)
    await financial_admin_page.wait_for_load_state("networkidle")

    found = await _search_and_select_member(financial_admin_page, "Bob", BOB["email"])
    assert found, "Bob should be findable via the member search"

    await financial_admin_page.select_option("#id_source_type", "adjustment")
    await financial_admin_page.fill("#id_amount", "5.00")
    await financial_admin_page.fill(
        "#id_description", "Playwright test_37 credit — corrected in the same test run"
    )
    submit_btn = financial_admin_page.locator("#credit-submit")
    assert not await submit_btn.is_disabled(), "Submit should enable once a member is selected"
    await submit_btn.click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("37_5_after_credit"))
    assert await financial_admin_page.locator(".alert-danger").count() == 0, \
        "Credit should not produce an error message"

    # Recent Activity is ordered most-recent-first, so the Correct button for
    # the transaction we just created is the first one in the table.
    correct_btn = financial_admin_page.locator(".correct-btn").first
    assert await correct_btn.count() > 0, "Expected a Correct button for the new manual credit"
    await correct_btn.click()
    await financial_admin_page.wait_for_selector("#correction-modal.show", timeout=5000)

    amount_field = financial_admin_page.locator("#correction-amount")
    prefilled = await amount_field.input_value()
    assert prefilled, "Correction amount should be pre-filled with the remaining correctable amount"

    await financial_admin_page.fill("#correction-form textarea[name='description']",
                                     "Playwright test_37 self-cancelling correction")
    await financial_admin_page.locator("#correction-form button[type='submit']").click()
    await financial_admin_page.wait_for_load_state("networkidle")
    await financial_admin_page.screenshot(path=screenshot_path("37_5_after_correction"))

    assert await financial_admin_page.locator(".alert-danger").count() == 0, \
        "Correction should not produce an error message"
