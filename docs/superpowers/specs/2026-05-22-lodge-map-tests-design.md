# Lodge Map Booking Tests — Design Spec
**Date:** 2026-05-22
**File to create:** `tests/test_29_lodge_map.py`

---

## Context

The CSC booking system added an interactive SVG lodge map as a second way to select rooms on the availability page (`/bookings/check_availability/`). The map is a client-side view toggle — same URL, same form submission, different room-selection UX. Existing tests (`test_04`, `test_05`, `test_06`) cover the card-view booking flow. This file covers the map-view flow.

---

## Fixture Design

### `alice_map_page` (function-scoped, async)

Builds on the existing `alice_page` fixture (authenticated Alice session):

1. Navigate to `AVAILABILITY_URL`
2. Set check-in/check-out dates (~30 days out, same pattern as `test_04`)
3. Submit the date search, wait for `networkidle`
4. Click `#view-toggle-map`
5. Wait for `#lodge-map-host` to be visible

**Tests that touch cart state or trigger AJAX date changes** use `alice_page` directly and do their own setup to avoid state bleed between tests.

---

## Test Inventory (~15 tests)

### Map Rendering

| Test ID | What it verifies |
|---------|-----------------|
| `test_29_1_map_view_toggle` | Clicking `#view-toggle-map` shows `#lodge-map-host`; card grid is hidden |
| `test_29_2_map_renders_rooms` | At least one `.lm-room[data-state="available"]` exists in the SVG |
| `test_29_3_map_legend_visible` | Legend swatches (`.lm-swatch`) for available, assigned, unavailable states are present |

### Popover Interactions

| Test ID | What it verifies |
|---------|-----------------|
| `test_29_4_click_room_opens_popover` | Clicking an available `.lm-room` reveals `#lodge-map-popover` with a non-empty title |
| `test_29_5_room_color_changes_on_assignment` | Selecting occupant inside popover changes `.lm-room-rect` fill from `#d6efdc` (available) to `#bcdcf2` (assigned) |
| `test_29_6_popover_done_closes` | Clicking `#lodge-map-popover-done` hides the popover |
| `test_29_7_popover_x_closes` | Clicking `#lodge-map-popover-close` hides the popover |

### Filtering

| Test ID | What it verifies |
|---------|-----------------|
| `test_29_8_location_filter_applies_to_map` | Changing `#location-filter` selection updates which rooms are visible/interactive on the map |

### Keyboard & Accessibility

| Test ID | What it verifies |
|---------|-----------------|
| `test_29_9_keyboard_enter_opens_popover` | Focusing an available `.lm-room` (tabindex="0") and pressing Enter opens the popover |
| `test_29_10_keyboard_escape_closes_popover` | Pressing Escape while popover is open closes it |
| `test_29_11_unavailable_room_not_clickable` | `.lm-room[data-state="unavailable"]` has `tabindex="-1"`; clicking it does not open the popover |

### Booking Completion

| Test ID | What it verifies |
|---------|-----------------|
| `test_29_12_full_map_booking_to_cart` | Full flow: toggle map → click room → assign Alice → Done → Add to Cart → `CART_URL` shows a booking |
| `test_29_13_family_member_booking_via_map` | Same flow but select a different club member (e.g., Bob) as occupant in the popover dropdown |
| `test_29_14_guest_booking_via_map` | Same flow but target a Private room (`data-room="R1/R2/R3"`) and select a guest occupant |
| `test_29_15_ajax_date_change_closes_popover` | Opening popover then changing dates via AJAX closes the popover and rebuilds the map |

---

## Assertion Patterns

| What to check | How |
|---------------|-----|
| Popover visible/hidden | `expect(page.locator("#lodge-map-popover")).to_be_visible()` / `to_be_hidden()` |
| Room state attribute | `locator.get_attribute("data-state")` == `"available"` / `"assigned"` |
| Room color fill | `locator(".lm-room-rect").get_attribute("fill")` — `#d6efdc` (available), `#bcdcf2` (assigned) |
| Rooms rendered | `.lm-room` count > 0 |
| Cart content | `page.content()` contains "cart"/"booking" keywords after navigating to `CART_URL` |
| tabindex | `locator.get_attribute("tabindex")` == `"-1"` for unavailable rooms |

**Wait strategy:**
- `wait_for_load_state("networkidle")` after form submits
- `page.wait_for_selector("#lodge-map-host", state="visible")` after toggling to map
- `page.wait_for_selector("#lodge-map-popover", state="visible"/"hidden")` for popover transitions
- `wait_for_timeout(1000)` after JS-driven map rebuilds (AJAX date change)

Screenshots saved for every test via `screenshot_path()`.

---

## Key Gotchas

- **DOM movement**: the `.room-card` is physically moved into `#lodge-map-popover-body` when a room is clicked. Select the occupant via `#lodge-map-popover-body select.member-select`, not from the card grid.
- **Guest booking** (`test_29_14`): only Private rooms (`data-room="R1"`, `R2`, `R3`) accept guest occupants. Target these specifically.
- **Family member booking** (`test_29_13`): "family member" means selecting any other club member (e.g., Bob) from the occupant dropdown — not a dependent. No extra seed setup required; Bob already exists.
- **Unavailable room clicks**: assert popover is NOT visible after click — don't assert an error or redirect.
- **Location filter + map**: the filter hides/shows `.room-card` elements; the map reflects this by updating which `.lm-room` elements are rendered or marked unavailable.

---

## Files to Create/Update

| File | Action |
|------|--------|
| `tests/test_29_lodge_map.py` | Create — new test file |
| `CLAUDE.md` | Update test coverage table to include section 29 |
