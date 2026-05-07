"""Section 1 — Test Environment Setup"""
import pytest
from playwright.async_api import Page
from tests.helpers import BASE_URL, ALICE, BOB, screenshot_path, login, LOGIN_URL


@pytest.mark.asyncio
async def test_1_site_loads(page: Page):
    """Site loads without error."""
    resp = await page.goto(BASE_URL)
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    await page.screenshot(path=screenshot_path("01_site_loads"))


@pytest.mark.asyncio
async def test_1_alice_login(page: Page):
    """Alice can log in."""
    await login(page, ALICE["email"], ALICE["password"])
    await page.screenshot(path=screenshot_path("01_alice_login"))
    assert "/login" not in page.url, f"Still on login page: {page.url}"


@pytest.mark.asyncio
async def test_1_bob_login(page: Page):
    """Bob can log in."""
    await login(page, BOB["email"], BOB["password"])
    await page.screenshot(path=screenshot_path("01_bob_login"))
    assert "/login" not in page.url, f"Still on login page: {page.url}"


@pytest.mark.asyncio
async def test_1_wrong_password_rejected(page: Page):
    """Login fails with wrong password."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="email"]', ALICE["email"])
    await page.fill('input[name="password"]', "WrongPass!")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path("01_wrong_password"))
    # Still on sign-in page OR shows an error
    assert "sign-in" in page.url or await page.locator(".errorlist, .alert-danger, [class*=error]").count() > 0
