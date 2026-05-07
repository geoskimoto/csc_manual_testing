"""Section 21 — Mobile / Responsive Testing"""
import pytest
from playwright.async_api import Browser
from tests.helpers import BASE_URL, ALICE, login, screenshot_path

VIEWPORTS = [
    ("phone",  {"width": 375,  "height": 812}),
    ("tablet", {"width": 768,  "height": 1024}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("label,viewport", VIEWPORTS)
async def test_21_responsive_dashboard(browser: Browser, label: str, viewport: dict):
    """Dashboard renders without horizontal overflow on phone and tablet."""
    context = await browser.new_context(viewport=viewport)
    page = await context.new_page()
    await login(page, ALICE["email"], ALICE["password"])
    await page.goto(f"{BASE_URL}/dashboard/")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path(f"21_{label}_dashboard"), full_page=True)

    # Check scroll width vs viewport width (overflow = layout broken)
    overflow = await page.evaluate("""() => {
        return document.documentElement.scrollWidth > window.innerWidth;
    }""")
    assert not overflow, f"Horizontal overflow on {label} ({viewport['width']}px)"
    await context.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("label,viewport", VIEWPORTS)
async def test_21_responsive_availability(browser: Browser, label: str, viewport: dict):
    """Availability page renders on small screens."""
    context = await browser.new_context(viewport=viewport)
    page = await context.new_page()
    await login(page, ALICE["email"], ALICE["password"])
    await page.goto(f"{BASE_URL}/bookings/availability/")
    await page.wait_for_load_state("networkidle")
    await page.screenshot(path=screenshot_path(f"21_{label}_availability"), full_page=True)
    overflow = await page.evaluate("""() => {
        return document.documentElement.scrollWidth > window.innerWidth;
    }""")
    assert not overflow, f"Horizontal overflow on availability at {label} ({viewport['width']}px)"
    await context.close()
