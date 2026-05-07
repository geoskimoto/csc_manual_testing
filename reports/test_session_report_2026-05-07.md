# CSC Booking System — Test Session Report
**Date:** 2026-05-07
**Engineer:** Nick Steele

---

## Session Overview

Full Playwright test suite expansion and hardening session. Started with ~70 passing tests across ~7 sections; ended with 119 passing, 3 skipped, 0 failed across 122 total tests spanning 18 sections. Built out all missing test sections, fixed infrastructure gaps, and resolved a persistent Stripe cart exhaustion bug.

---

## Test Runs

| Run | Passed | Failed | Skipped | Total | Notes |
|-----|--------|--------|---------|-------|-------|
| 1 (baseline) | 68 | 0 | 2 | 70 | Before session improvements |
| 2 | 70 | 0 | 2 | 72 | After room-index staggering fix |
| 3 | 112 | 0 | 3 | 115 | After 8 new sections written |
| 4 (final) | 119 | 0 | 3 | 122 | After seed cleanup + test_13_4 fix |

---

## What Was Built

### New Test Sections (50 new tests)

| Section | File | Tests | Description |
|---------|------|-------|-------------|
| 2 | `test_02_registration.py` | 8 | Sign-up, membership application, login, password reset, credential validation |
| 5 | `test_05_family_booking.py` | 5 | Family profile, availability search with member-selects, multi-room selection |
| 6 | `test_06_guest_booking.py` | 4 | Guest options in availability, add to cart, occupant info at checkout |
| 12 | `test_12_admin_booking.py` | 8 | Admin booking dashboard, availability, member search, cart, checkout, transactions |
| 13 | `test_13_admin_manage.py` | 6 | Admin manage-bookings list, booking detail modal (AJAX fetch), access control |
| 15 | `test_15_invoicing.py` | 7 | My-invoices, billing admin dashboard, access control by role, receipt invoices |
| 22 | `test_22_cross_browser.py` | 9 | Firefox and WebKit: public pages, login flow, availability search |
| 23 | `test_23_race_conditions.py` | 3 | Concurrent cart adds (Alice + Bob), rapid sequential adds, cart isolation |

---

## Infrastructure Built

### Seed Data (`seed_test_data.py`)

Extended the `seed_test_data` management command with two new steps:

**Step 6 — Admin Test Accounts**
- `booking.admin@csc-test.local` / `AdminPass99!` — Booking Administrators group, `is_staff=False`
- `financial.admin@csc-test.local` / `AdminPass99!` — Financial Administrators group, `is_staff=True`
- Both accounts get a Profile for template rendering

**Step 7 — Cleanup Stale Test Artifacts**
- Deletes expired `reserved` cart items (TTL passed)
- Cancels any confirmed bookings for Alice/Bob that were created by payment tests (i.e., not seeded by the command itself)
- Seeded bookings are identified by `success_id` prefix (`seed_past_alice`, `seed_future_alice`) and are preserved

### Test Helpers (`helpers.py`)

Added:
- `BOOKING_ADMIN` and `FINANCIAL_ADMIN` credential dictionaries
- URL constants for all new test sections: `SIGN_UP_URL`, `MEMBERSHIP_APP_URL`, `MY_INVOICES_URL`, `SUBSCRIPTIONS_URL`, `ADMIN_AVAIL_URL`, `ADMIN_CART_URL`, `ADMIN_CHECKOUT_URL`, `ADMIN_TXNS_URL`, `ADMIN_SEARCH_URL`, `BILLING_ADMIN_URL`, `BILLING_CREATE_URL`, `SUBS_ADMIN_URL`

### Test Fixtures (`conftest.py`)

Added `booking_admin_page` and `financial_admin_page` fixtures using the new admin credential dictionaries.

### Browser Support

- Confirmed Playwright Chromium works headless
- Installed Firefox (requires `libgtk-3-0t64`, `libpangocairo-1.0-0`, `libcairo-gobject2`)
- Installed WebKit via `.venv/bin/playwright install-deps webkit`

---

## Bugs Fixed

### 1. Stripe Cart Exhaustion (Room Staggering)

**Problem:** All Stripe payment tests (8_1 through 8_5) were targeting the same first available bunk. After `test_8_1` confirmed a booking for Alice, she was marked in `conflicted_profile_ids` for those dates. Subsequent tests found her disabled and fell back to Bob, but Bob is not a valid occupant for Alice's session.

**Fix:** `_add_room_to_cart()` now accepts a `room_index: int = 0` parameter and targets the Nth `select.member-select` element and corresponding form/button. Each test in the payment suite uses a unique index (0–4), so they compete for different bunks rather than piling onto the first one.

**Room inventory context:** The lodge has ~50+ bunks across sections A100–A115, S116–S127, C19–C45, M01–M18, W46–W57. The index staggering will handle many test runs before exhaustion becomes an issue again.

### 2. Disabled Occupant Option Skip

**Problem:** Some `<option>` elements in the member-select dropdown are disabled when an occupant is already booked. Selecting a disabled option causes the form submission to use an invalid value.

**Fix:** Added a check for `await opt.get_attribute("disabled")` before selecting an option. The helper now skips disabled options and finds the first valid, enabled one.

### 3. `test_13_4` Wrong Selector (Admin Booking Detail Modal)

**Problem:** Test looked for `a[href*='/admin-bookings/booking-detail/']` to open a booking detail page. The manage-bookings page does not use anchor links — it uses JavaScript fetch triggered by `button.view-details-btn` to load detail JSON into a Bootstrap modal.

**Fix:** Changed selector to `button.view-details-btn`, clicks the button, waits 2 seconds for the AJAX fetch to complete, then asserts modal content is present.

---

## Remaining Skips & Known Gaps

### `test_8_2_stripe_declined_card` — Within-Run Skip

**Status:** Skips within the same test run if `test_8_1` ran first.

**Root cause:** `test_8_1` confirms Alice's booking for the payment test dates, putting Alice in `conflicted_profile_ids`. Within that same run, Alice has no available occupant slot for `test_8_2`'s checkout. The `seed_test_data` cleanup only runs between runs, so Alice is still conflicted during the same run.

**Workaround:** On the next run, `seed_test_data` cancels the test booking from `test_8_1`, freeing Alice. `test_8_2` then passes.

**Structural fix needed:** Assign `test_8_2` its own isolated date window (not shared with `test_8_1`) so the tests are truly independent within a single run.

### `test_15_4_billing_admin_blocked_for_booking_admin` — Real Bug (Deferred)

**Status:** Skipped with a note. Underlying application bug is real but deferred.

**Issue:** `/billing/admin-tool/` returns HTTP 200 for `booking_admin` users. The billing admin dashboard should be restricted to `financial_admin` (Financial Administrators group) only. This is a privilege escalation risk — a booking admin can view billing data they should not have access to.

**Files to fix:**
- `invoicing/views.py` — check the view's decorator or permission mixin
- `userauths/permissions.py` — confirm `is_financial_administrator()` vs `is_booking_administrator()` guards

**Decision needed:** Confirm with product team whether booking admins intentionally have billing visibility before changing the permission check. If intentional, the test assertion should be updated to reflect the actual policy.

### `test_16_4_individual_notification_mark_read` — Data Gap (Deferred)

**Status:** Skipped because `test_16_3` bulk-marks all notifications as read first, consuming the single seeded unread notification.

**Fix needed:** `seed_test_data` should create two unread notifications for Alice so `test_16_3` and `test_16_4` each have an independent target. Deferred per user decision.

---

## Recommendations

1. **Fix `test_8_2` date isolation.** Assign the declined-card Stripe test its own date window (e.g., +35/+37 days instead of sharing with `test_8_1` at +30/+32 days). This makes the two payment tests fully independent within a single run.

2. **Decision on billing admin access control.** Confirm the intended role boundary with the product team. If `booking_admin` should not access `/billing/admin-tool/`, fix the view decorator in `invoicing/views.py`. If they should have access, update the test to reflect actual policy.

3. **Add second seeded notification.** Update `seed_test_data` to create two unread notifications for Alice. This unblocks `test_16_4` without depending on test ordering.

4. **Expand cross-browser coverage to authenticated flows.** `test_22` currently covers only public pages and login. Add at least one authenticated flow (dashboard load, availability search while logged in) under Firefox and WebKit to catch rendering regressions in member-facing UI.

---

## Final State

```
119 passed, 3 skipped, 0 failed — 122 total tests
```

Test sections covered: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 22, 23
