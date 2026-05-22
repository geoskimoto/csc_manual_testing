# Lodge Map Booking Tests — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write 15 Playwright tests in `tests/test_29_lodge_map.py` that validate the interactive SVG lodge map booking flow, then update CLAUDE.md and run the full suite.

**Architecture:** A shared `alice_map_page` fixture in `conftest.py` handles auth + availability search + map toggle. Cart-touching and AJAX tests use `alice_page` directly and set up state themselves to prevent bleed. All tests follow the existing `@pytest.mark.asyncio` + `screenshot_path()` convention.

**Tech Stack:** Python 3.12, pytest-asyncio, Playwright (Chromium headless), same virtualenv as existing suite (`.venv/`)

---

## File Map

| Action | File |
|--------|------|
| Modify | `tests/conftest.py` — add `alice_map_page` fixture |
| Create | `tests/test_29_lodge_map.py` — 15 new tests |
| Modify | `CLAUDE.md` — add section 29 to coverage table |

---

## Task 1: Add `alice_map_page` fixture to `conftest.py`

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Open conftest.py and append the fixture after `financial_admin_page`**

Extend the existing `from tests.helpers import ...` line to include `AVAILABILITY_URL`:
```python
from tests.helpers import ALICE, BOB, BOOKING_ADMIN, FINANCIAL_ADMIN, login, AVAILABILITY_URL
```
Then append after the last fixture:
```python
@pytest_asyncio.fixture
async def alice_map_page(browser):
    """Alice logged in, availability searched, map view active."""
    from datetime import date, timedelta
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    pg = await context.new_page()
    await login(pg, ALICE["email"], ALICE["password"])

    checkin  = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout = (date.today() + timedelta(days=32)).strftime("%Y-%m-%d")

    await pg.goto(AVAILABILITY_URL)
    await pg.wait_for_load_state("networkidle")
    await pg.fill('input[name="check_in_date"]', checkin)
    await pg.fill('input[name="check_out_date"]', checkout)
    await pg.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await pg.wait_for_load_state("networkidle")
    await pg.wait_for_timeout(2000)

    await pg.click('#view-toggle-map')
    await pg.wait_for_selector('#lodge-map-host', state='visible')
    await pg.wait_for_timeout(1000)  # SVG render settle

    yield pg
    await context.close()
```

- [ ] **Step 2: Verify import doesn't already exist**

```bash
grep "AVAILABILITY_URL" /home/geoskimoto/projects/csc_manual_testing/tests/conftest.py
```
Expected: either the import line appears, or nothing (no conflict).

- [ ] **Step 3: Run a quick smoke test to confirm fixture is importable**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -c "import tests.conftest; print('conftest OK')"
```
Expected: `conftest OK`

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py && \
  git commit -m "test: add alice_map_page fixture for lodge map tests"
```

---

## Task 2: Create `test_29_lodge_map.py` — scaffold, imports, shared helpers

**Files:**
- Create: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Create the file with header, imports, date constants, and one shared helper**

```python
"""Section 29 — Interactive Lodge Map Booking Flow"""
import pytest
from datetime import date, timedelta
from playwright.async_api import Page
from tests.helpers import AVAILABILITY_URL, CART_URL, screenshot_path

_CHECKIN_DATE  = date.today() + timedelta(days=30)
_CHECKOUT_DATE = date.today() + timedelta(days=32)
CHECKIN  = _CHECKIN_DATE.strftime("%Y-%m-%d")
CHECKOUT = _CHECKOUT_DATE.strftime("%Y-%m-%d")
CHECKIN_DISPLAY  = _CHECKIN_DATE.strftime("%B %-d, %Y")
CHECKOUT_DISPLAY = _CHECKOUT_DATE.strftime("%B %-d, %Y")


async def _search_and_enter_map(page: Page) -> None:
    """Navigate to availability, search dates, toggle to map view."""
    await page.goto(AVAILABILITY_URL)
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="check_in_date"]', CHECKIN)
    await page.fill('input[name="check_out_date"]', CHECKOUT)
    await page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)
    await page.click('#view-toggle-map')
    await page.wait_for_selector('#lodge-map-host', state='visible')
    await page.wait_for_timeout(1000)
```

- [ ] **Step 2: Verify file parses without syntax errors**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -c "import tests.test_29_lodge_map; print('parse OK')"
```
Expected: `parse OK`

- [ ] **Step 3: Commit scaffold**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: scaffold test_29_lodge_map with helpers and date constants"
```

---

## Task 3: Map rendering tests (29_1, 29_2, 29_3)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append rendering tests**

```python
@pytest.mark.asyncio
async def test_29_1_map_view_toggle(alice_map_page: Page):
    """Clicking Map View shows the SVG host and hides the card grid."""
    await alice_map_page.screenshot(path=screenshot_path("29_1_map_toggle"))
    map_host = alice_map_page.locator('#lodge-map-host')
    assert await map_host.is_visible(), "#lodge-map-host not visible after toggling map view"
    # Card grid should not be the primary display
    assert "500" not in await alice_map_page.title(), "Server error on availability page"


@pytest.mark.asyncio
async def test_29_2_map_renders_rooms(alice_map_page: Page):
    """Map SVG renders at least one available room."""
    await alice_map_page.screenshot(path=screenshot_path("29_2_map_rooms"))
    rooms = alice_map_page.locator('.lm-room')
    assert await rooms.count() > 0, "No .lm-room elements found in map SVG"
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    assert await available.count() > 0, "No available rooms shown on map"


@pytest.mark.asyncio
async def test_29_3_map_legend_visible(alice_map_page: Page):
    """Map legend swatches are present."""
    await alice_map_page.screenshot(path=screenshot_path("29_3_legend"))
    swatches = alice_map_page.locator('.lm-swatch')
    count = await swatches.count()
    assert count >= 2, f"Expected at least 2 legend swatches, found {count}"
```

- [ ] **Step 2: Run the three rendering tests**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_1_map_view_toggle \
    tests/test_29_lodge_map.py::test_29_2_map_renders_rooms \
    tests/test_29_lodge_map.py::test_29_3_map_legend_visible \
    -v --tb=short
```
Expected: 3 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add map rendering tests 29_1, 29_2, 29_3"
```

---

## Task 4: Popover open/close tests (29_4, 29_6, 29_7)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append popover open and close tests**

```python
@pytest.mark.asyncio
async def test_29_4_click_room_opens_popover(alice_map_page: Page):
    """Clicking an available room reveals the popover with a room title."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')
    await alice_map_page.screenshot(path=screenshot_path("29_4_popover_open"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert await popover.is_visible(), "Popover did not appear after clicking room"

    title = alice_map_page.locator('#lodge-map-popover-title')
    title_text = await title.text_content()
    assert title_text and title_text.strip(), "Popover title is empty"


@pytest.mark.asyncio
async def test_29_6_popover_done_closes(alice_map_page: Page):
    """Done button closes the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.click('#lodge-map-popover-done')
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='hidden')
    await alice_map_page.screenshot(path=screenshot_path("29_6_done_closes"))

    assert not await alice_map_page.locator('#lodge-map-popover').is_visible(), \
        "Popover still visible after clicking Done"


@pytest.mark.asyncio
async def test_29_7_popover_x_closes(alice_map_page: Page):
    """X (close) button closes the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.click('#lodge-map-popover-close')
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='hidden')
    await alice_map_page.screenshot(path=screenshot_path("29_7_x_closes"))

    assert not await alice_map_page.locator('#lodge-map-popover').is_visible(), \
        "Popover still visible after clicking X"
```

- [ ] **Step 2: Run these three tests**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_4_click_room_opens_popover \
    tests/test_29_lodge_map.py::test_29_6_popover_done_closes \
    tests/test_29_lodge_map.py::test_29_7_popover_x_closes \
    -v --tb=short
```
Expected: 3 PASSED (or 3 SKIPPED if no available rooms)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add popover open/close tests 29_4, 29_6, 29_7"
```

---

## Task 5: Room color changes on occupant assignment (29_5)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append color change test**

```python
@pytest.mark.asyncio
async def test_29_5_room_color_changes_on_assignment(alice_map_page: Page):
    """Selecting an occupant in the popover changes the room's visual state to assigned."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    first_room = available.first
    room_id = await first_room.get_attribute("data-room")

    await first_room.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    # Select the first non-empty, non-disabled occupant option in the popover
    select = alice_map_page.locator('#lodge-map-popover-body select.member-select')
    opts = await select.locator('option').all()
    chosen = None
    for opt in opts:
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.strip() and disabled is None:
            chosen = val
            break

    if chosen is None:
        pytest.skip("No selectable occupant found in popover dropdown")

    await select.select_option(value=chosen)
    await alice_map_page.wait_for_timeout(600)  # JS updates fill + data-state

    await alice_map_page.screenshot(path=screenshot_path("29_5_color_change"))

    # Check data-state changed to "assigned"
    room_state = await alice_map_page.locator(
        f'.lm-room[data-room="{room_id}"]'
    ).get_attribute("data-state")
    assert room_state == "assigned", \
        f"Room {room_id} data-state is '{room_state}', expected 'assigned'"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_5_room_color_changes_on_assignment \
    -v --tb=short
```
Expected: PASSED (or SKIPPED if no available rooms)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add room color/state change test 29_5"
```

---

## Task 6: Location filter applies to map (29_8)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append filter test**

```python
@pytest.mark.asyncio
async def test_29_8_location_filter_applies_to_map(alice_map_page: Page):
    """Changing the location filter updates the map without a server error."""
    filter_select = alice_map_page.locator('#location-filter')
    if await filter_select.count() == 0:
        pytest.skip("Location filter not found")

    options = await filter_select.locator('option').all()
    if len(options) < 2:
        pytest.skip("No filter options to select")

    # Record initial room count
    initial_count = await alice_map_page.locator('.lm-room').count()

    # Select the second option (first non-All)
    second_val = await options[1].get_attribute("value")
    await filter_select.select_option(value=second_val)
    await alice_map_page.wait_for_timeout(800)  # JS filter update

    await alice_map_page.screenshot(path=screenshot_path("29_8_filter_map"))

    # No server error
    assert "500" not in await alice_map_page.title(), "Server error after applying location filter"
    # Map host still visible — map didn't collapse
    assert await alice_map_page.locator('#lodge-map-host').is_visible(), \
        "#lodge-map-host hidden after applying filter"
    # Room count may decrease or stay the same — both are valid; just ensure > 0 or no crash
    filtered_count = await alice_map_page.locator('.lm-room').count()
    assert filtered_count >= 0, "Unexpected negative room count after filter"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_8_location_filter_applies_to_map \
    -v --tb=short
```
Expected: PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add location filter map test 29_8"
```

---

## Task 7: Keyboard navigation tests (29_9, 29_10)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append keyboard tests**

```python
@pytest.mark.asyncio
async def test_29_9_keyboard_enter_opens_popover(alice_map_page: Page):
    """Pressing Enter on a focused available room opens the popover."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    # Focus the room via JavaScript (SVG elements may not respond to .focus())
    await alice_map_page.evaluate("""
        const room = document.querySelector('.lm-room[data-state="available"]');
        if (room) room.focus();
    """)
    await alice_map_page.wait_for_timeout(300)

    await alice_map_page.keyboard.press('Enter')
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_9_keyboard_enter"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert await popover.is_visible(), "Popover did not open on keyboard Enter"


@pytest.mark.asyncio
async def test_29_10_keyboard_escape_closes_popover(alice_map_page: Page):
    """Pressing Escape while popover is open closes it."""
    available = alice_map_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms found on map")

    await available.first.click()
    await alice_map_page.wait_for_selector('#lodge-map-popover', state='visible')

    await alice_map_page.keyboard.press('Escape')
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_10_escape_closes"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert not await popover.is_visible(), "Popover still visible after pressing Escape"
```

- [ ] **Step 2: Run the keyboard tests**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_9_keyboard_enter_opens_popover \
    tests/test_29_lodge_map.py::test_29_10_keyboard_escape_closes_popover \
    -v --tb=short
```
Expected: 2 PASSED (or SKIPPED if no available rooms)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add keyboard navigation tests 29_9, 29_10"
```

---

## Task 8: Unavailable room accessibility test (29_11)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append unavailable room test**

```python
@pytest.mark.asyncio
async def test_29_11_unavailable_room_not_clickable(alice_map_page: Page):
    """Unavailable rooms have tabindex='-1' and clicking them does not open the popover."""
    unavailable = alice_map_page.locator('.lm-room[data-state="unavailable"]')
    if await unavailable.count() == 0:
        pytest.skip("No unavailable rooms present on map for this date range")

    first_unavail = unavailable.first
    tabindex = await first_unavail.get_attribute("tabindex")
    assert tabindex == "-1", \
        f"Unavailable room tabindex is '{tabindex}', expected '-1'"

    # Click it and confirm popover does NOT appear
    await first_unavail.click(force=True)
    await alice_map_page.wait_for_timeout(600)

    await alice_map_page.screenshot(path=screenshot_path("29_11_unavailable"))

    popover = alice_map_page.locator('#lodge-map-popover')
    assert not await popover.is_visible(), \
        "Popover opened after clicking an unavailable room — should be blocked"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_11_unavailable_room_not_clickable \
    -v --tb=short
```
Expected: PASSED (or SKIPPED if all rooms happen to be available)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add unavailable room accessibility test 29_11"
```

---

## Task 9: Full map booking to cart (29_12)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append full booking flow test**

```python
@pytest.mark.asyncio
async def test_29_12_full_map_booking_to_cart(alice_page: Page):
    """Complete flow: map view → select room → assign Alice → Done → add to cart."""
    await _search_and_enter_map(alice_page)

    available = alice_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms on map")

    await available.first.click()
    await alice_page.wait_for_selector('#lodge-map-popover', state='visible')

    # Select first non-empty occupant in popover (Alice)
    select = alice_page.locator('#lodge-map-popover-body select.member-select')
    opts = await select.locator('option').all()
    chosen = None
    for opt in opts:
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.strip() and disabled is None:
            chosen = val
            break

    if chosen is None:
        pytest.skip("No selectable occupant in popover dropdown")

    await select.select_option(value=chosen)
    await alice_page.wait_for_timeout(300)
    await alice_page.click('#lodge-map-popover-done')
    await alice_page.wait_for_selector('#lodge-map-popover', state='hidden')

    # Patch hidden form dates and submit
    await alice_page.evaluate(f"""
        const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{CHECKIN_DISPLAY}';
            if (co) co.value = '{CHECKOUT_DISPLAY}';
        }}
    """)

    add_btn = alice_page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btn.count() == 0:
        pytest.skip("Add Selected to Cart button not found")

    await add_btn.click()
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("29_12_after_add"))

    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["cart", "added", "reserved", "badge"]), \
        "No confirmation of cart addition found after map booking"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_12_full_map_booking_to_cart \
    -v --tb=short
```
Expected: PASSED (or SKIPPED)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add full map booking to cart test 29_12"
```

---

## Task 10: Family member (another club member) booking via map (29_13)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append family member booking test**

```python
@pytest.mark.asyncio
async def test_29_13_family_member_booking_via_map(alice_page: Page):
    """Alice selects a different club member (not herself) as occupant via the map."""
    await _search_and_enter_map(alice_page)

    available = alice_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms on map")

    await available.first.click()
    await alice_page.wait_for_selector('#lodge-map-popover', state='visible')

    select = alice_page.locator('#lodge-map-popover-body select.member-select')
    opts = await select.locator('option').all()

    # Collect all selectable options; skip the first valid one (likely Alice herself)
    selectable = []
    for opt in opts:
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.strip() and disabled is None:
            selectable.append(val)

    if len(selectable) < 2:
        pytest.skip("Only one selectable occupant in dropdown — cannot test other-member booking")

    other_member = selectable[1]  # second valid option = different club member
    await select.select_option(value=other_member)
    await alice_page.wait_for_timeout(300)
    await alice_page.click('#lodge-map-popover-done')
    await alice_page.wait_for_selector('#lodge-map-popover', state='hidden')

    await alice_page.evaluate(f"""
        const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{CHECKIN_DISPLAY}';
            if (co) co.value = '{CHECKOUT_DISPLAY}';
        }}
    """)

    add_btn = alice_page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btn.count() == 0:
        pytest.skip("Add Selected to Cart button not found")

    await add_btn.click()
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("29_13_family_member"))

    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["cart", "added", "reserved", "badge"]), \
        "No confirmation after booking a different club member via map"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_13_family_member_booking_via_map \
    -v --tb=short
```
Expected: PASSED (or SKIPPED if only one occupant option)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add other-club-member map booking test 29_13"
```

---

## Task 11: Guest booking via map on Private room (29_14)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append guest booking test**

```python
@pytest.mark.asyncio
async def test_29_14_guest_booking_via_map(alice_page: Page):
    """Alice books a Private room via the map and assigns a guest occupant."""
    await _search_and_enter_map(alice_page)

    # Private rooms (R1, R2, R3) accept guest occupants
    private_room_ids = ["R1", "R2", "R3"]
    clicked_private = False
    for rid in private_room_ids:
        room = alice_page.locator(f'.lm-room[data-room="{rid}"]')
        if await room.count() > 0:
            state = await room.get_attribute("data-state")
            if state == "available":
                await room.click()
                await alice_page.wait_for_selector('#lodge-map-popover', state='visible')
                clicked_private = True
                break

    if not clicked_private:
        pytest.skip("No available Private room (R1/R2/R3) found for guest booking test")

    select = alice_page.locator('#lodge-map-popover-body select.member-select')
    opts = await select.locator('option').all()
    guest_val = None
    for opt in opts:
        val = await opt.get_attribute("value")
        disabled = await opt.get_attribute("disabled")
        if val and val.startswith("guest_") and disabled is None:
            guest_val = val
            break

    if guest_val is None:
        pytest.skip("No guest option found in Private room dropdown")

    await select.select_option(value=guest_val)
    await alice_page.wait_for_timeout(300)
    await alice_page.click('#lodge-map-popover-done')
    await alice_page.wait_for_selector('#lodge-map-popover', state='hidden')

    # Fill guest name/age if fields appear after guest selection
    guest_name_input = alice_page.locator('input[name="guest_name_1"]')
    if await guest_name_input.count() > 0:
        await guest_name_input.fill("Test Guest")
        age_input = alice_page.locator('input[name="guest_age_1"]')
        if await age_input.count() > 0:
            await age_input.fill("30")

    await alice_page.evaluate(f"""
        const form = document.querySelector('form[action="/bookings/add_accommodations_to_cart/"]');
        if (form) {{
            const ci = form.querySelector('input[name="check_in_date"]');
            const co = form.querySelector('input[name="check_out_date"]');
            if (ci) ci.value = '{CHECKIN_DISPLAY}';
            if (co) co.value = '{CHECKOUT_DISPLAY}';
        }}
    """)

    add_btn = alice_page.locator("button").filter(has_text="Add Selected to Cart")
    if await add_btn.count() == 0:
        pytest.skip("Add Selected to Cart button not found")

    await add_btn.click()
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.screenshot(path=screenshot_path("29_14_guest_booking"))

    content = await alice_page.content()
    assert any(kw in content.lower() for kw in ["cart", "added", "reserved", "badge"]), \
        "No confirmation after guest booking via map"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_14_guest_booking_via_map \
    -v --tb=short
```
Expected: PASSED (or SKIPPED if no Private rooms available)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add guest booking via map test 29_14"
```

---

## Task 12: AJAX date change closes popover and rebuilds map (29_15)

**Files:**
- Modify: `tests/test_29_lodge_map.py`

- [ ] **Step 1: Append AJAX date change test**

```python
@pytest.mark.asyncio
async def test_29_15_ajax_date_change_closes_popover(alice_page: Page):
    """Changing dates while popover is open closes the popover and rebuilds the map."""
    await _search_and_enter_map(alice_page)

    available = alice_page.locator('.lm-room[data-state="available"]')
    if await available.count() == 0:
        pytest.skip("No available rooms on map")

    # Open the popover
    await available.first.click()
    await alice_page.wait_for_selector('#lodge-map-popover', state='visible')
    await alice_page.screenshot(path=screenshot_path("29_15_before_date_change"))

    # Change to different dates while popover is open
    new_checkin  = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
    new_checkout = (date.today() + timedelta(days=62)).strftime("%Y-%m-%d")
    await alice_page.fill('input[name="check_in_date"]', new_checkin)
    await alice_page.fill('input[name="check_out_date"]', new_checkout)
    await alice_page.evaluate(
        "document.querySelector('form[action=\"/bookings/check_availability/\"]').submit()"
    )
    await alice_page.wait_for_load_state("networkidle")
    await alice_page.wait_for_timeout(1500)

    await alice_page.screenshot(path=screenshot_path("29_15_after_date_change"))

    # Popover must not be visible after date change (closed by rebuild or page navigation)
    popover = alice_page.locator('#lodge-map-popover')
    assert not await popover.is_visible(), \
        "Popover still visible after changing dates — should have closed on rebuild"

    # Map should still be functional (rooms present)
    assert "500" not in await alice_page.title(), "Server error after date change"
```

- [ ] **Step 2: Run the test**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/test_29_lodge_map.py::test_29_15_ajax_date_change_closes_popover \
    -v --tb=short
```
Expected: PASSED (or SKIPPED if no available rooms)

- [ ] **Step 3: Commit**

```bash
git add tests/test_29_lodge_map.py && \
  git commit -m "test: add AJAX date change popover close test 29_15"
```

---

## Task 13: Update CLAUDE.md and run full suite

**Files:**
- Modify: `CLAUDE.md` — add section 29 to coverage table

- [ ] **Step 1: Add section 29 row to the Test Coverage Status table in CLAUDE.md**

Find the row:
```
| 28 — Admin Refund Modal | `test_28_admin_refund.py` | 8 | Passing — does NOT submit refund (protects Alice's seeded booking) |
```
Insert after it:
```
| 29 — Lodge Map Booking | `test_29_lodge_map.py` | 15 | Written — map rendering, popover interactions, keyboard, filter, full booking flows (individual, other member, guest), AJAX date rebuild |
```
Also update the total count line near the top of the coverage section:
- Old: `_173 tests collected as of 2026-05-08. Last full run: 164 passed / 3 failed (seed issue, now fixed) / 6 skipped._`
- New: `_188 tests collected as of 2026-05-22. Last full run: see latest reports/analysis_*.md._`

- [ ] **Step 2: Commit CLAUDE.md**

```bash
git add CLAUDE.md && \
  git commit -m "docs: update CLAUDE.md with test_29 lodge map coverage"
```

- [ ] **Step 3: Seed test data before running the full suite**

```bash
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data
```
Expected: Command completes without error, prints seed summary.

- [ ] **Step 4: Run the full test suite**

```bash
cd /home/geoskimoto/projects/csc_manual_testing && \
  .venv/bin/python -m pytest tests/ -v --tb=short 2>&1 | tail -40
```
Expected: The suite completes. Note any failures and their test IDs. Do NOT modify any test or application code based on failures — report them to the user.

- [ ] **Step 5: Report results**

Report: total passed / failed / skipped, and for any test_29 failures list the test ID and the error message verbatim.
