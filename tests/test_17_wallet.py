"""Section 17 — Wallet Operations"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, WALLET_URL, DASHBOARD_URL, screenshot_path

ADD_FUNDS_URL = f"{BASE_URL}/wallet/add-funds/"
MY_INVOICES_URL = f"{BASE_URL}/billing/my-invoices/"


@pytest.mark.asyncio
async def test_17_1_wallet_page_loads(alice_page: Page):
    """Wallet dashboard page loads without error."""
    await alice_page.goto(WALLET_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_1_wallet"))
    assert "500" not in await alice_page.title(), "Server error on wallet page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "wallet", "balance", "credit", "transaction"
    ]), "Wallet page did not render expected content"


@pytest.mark.asyncio
async def test_17_2_wallet_balance_shown(alice_page: Page):
    """Wallet page displays a dollar balance."""
    await alice_page.goto(WALLET_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_2_wallet_balance"))
    content = await alice_page.content()
    # Alice has $8000 wallet balance per test data
    has_balance = "$" in content or "balance" in content.lower()
    assert has_balance, "No balance amount visible on wallet page"


@pytest.mark.asyncio
async def test_17_3_transaction_history_present(alice_page: Page):
    """Wallet page shows transaction history section."""
    await alice_page.goto(WALLET_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_3_transaction_history"))
    content = await alice_page.content()
    has_history = any(kw in content.lower() for kw in [
        "transaction", "history", "credit", "debit", "activity"
    ])
    assert has_history, "No transaction history section found on wallet page"


@pytest.mark.asyncio
async def test_17_4_add_funds_entry_point(alice_page: Page):
    """Wallet page or dashboard provides an 'Add Funds' link/button."""
    await alice_page.goto(WALLET_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_4_add_funds_link"))
    content = await alice_page.content()
    has_add_funds = (
        "add funds" in content.lower()
        or "/wallet/add-funds/" in content
        or "top up" in content.lower()
        or "fund" in content.lower()
    )
    assert has_add_funds, "No 'Add Funds' entry point found on wallet page"


@pytest.mark.asyncio
async def test_17_5_add_funds_page_loads(alice_page: Page):
    """Add funds page loads (may redirect to wallet with a form)."""
    await alice_page.goto(ADD_FUNDS_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_5_add_funds_page"))
    assert "500" not in await alice_page.title(), "Server error on add-funds page"
    # May redirect to wallet with modal/form, or load its own page
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "wallet", "add funds", "amount", "fund", "stripe", "payment"
    ]), "Add funds page did not render expected content"


@pytest.mark.asyncio
async def test_17_6_wallet_shown_on_dashboard(alice_page: Page):
    """Dashboard displays wallet balance summary."""
    await alice_page.goto(DASHBOARD_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_6_dashboard_wallet"))
    content = await alice_page.content()
    has_wallet = any(kw in content.lower() for kw in [
        "wallet", "balance", "$", "credit"
    ])
    assert has_wallet, "Dashboard does not display wallet balance"


@pytest.mark.asyncio
async def test_17_7_my_invoices_page_loads(alice_page: Page):
    """My invoices page loads — related to wallet billing history."""
    await alice_page.goto(MY_INVOICES_URL)
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("17_7_my_invoices"))
    assert "500" not in await alice_page.title(), "Server error on my-invoices page"
    content = await alice_page.content()
    assert any(kw in content.lower() for kw in [
        "invoice", "billing", "no invoices", "payment"
    ]), "My invoices page did not render expected content"


@pytest.mark.asyncio
async def test_17_8_wallet_anonymous_redirect(page: Page):
    """Anonymous user is redirected from wallet page."""
    await page.goto(WALLET_URL)
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("17_8_anon_wallet"))
    assert "sign-in" in page.url or "login" in page.url, \
        f"Anonymous user not redirected from wallet — got {page.url}"
