# Cycle 1 Plan — 2026-05-04

## Test Sections Run
All existing test files were run (full suite). No prior cycle recommendations existed, so the decision was to run everything and establish a baseline.

Files executed:
- `test_01_environment.py` — Login and environment checks
- `test_03_dashboard.py` — Dashboard rendering
- `test_04_booking_individual.py` — Individual booking flow
- `test_07_09_payment.py` — Wallet and Stripe payment flows
- `test_10_cancellation.py` — Booking cancellation
- `test_11_booking_history.py` — Booking history
- `test_14_subscriptions.py` — Subscription status
- `test_16_notifications.py` — Notification center
- `test_17_wallet.py` — Wallet operations
- `test_18_profile.py` — Profile management
- `test_19_security.py` — Access control / security
- `test_20_edge_cases.py` — Edge cases
- `test_21_responsive.py` — Responsive layout

## Results

| Outcome | Count |
|---------|-------|
| Passed  | 61    |
| Failed  | 4     |
| Skipped | 7     |
| Total   | 72    |

Run time: 6m 33s

## Failure Classifications

### real_bug (2)

**`test_16_3_mark_all_read_action`**
- Rationale: Playwright finds the "Mark all read" `<a>` element in the DOM but cannot click it because it is not visible. Alice has a seeded unread notification, so the element should be both present and interactable. The element existing in HTML but being invisible to users is a genuine UI bug — the button is inaccessible.
- This is NOT a test_bug: the test correctly uses `.filter(has_text="Mark all")` and skips if the count is zero; the element IS found (count > 0) but is simply not rendered visibly.

**`test_21_responsive_dashboard[phone-viewport0]`**
- Rationale: Explicitly listed as a known real bug in CLAUDE.md. The assertion is correct — `scrollWidth > clientWidth` means the page overflows horizontally at 375px. This is a genuine layout bug.

### test_bug (2)

**`test_8_1_stripe_success_payment`** and **`test_8_2_stripe_declined_card`**
- Rationale: The test fills the card number field successfully (inside the first Stripe iframe, using `[placeholder*="Card number"]`). Then it tries to fill the expiry field using the same `stripe_frame` (first iframe) — but that locator times out. Stripe's CardElement renders each input field (card number, expiry, CVC) in its own separate iframe. The test must target each field's iframe individually rather than assuming all fields are in the first iframe.
- This is NOT a real_bug: the Stripe checkout UI is presumably rendering correctly; the test's iframe-targeting strategy is too narrow.
- Action: Report to user for test redesign. Do NOT modify test files.

### missing_data (0)
None identified this cycle.

## Skipped Tests
7 tests were skipped. Typical reasons from prior analysis:
- Cart pre-fill helper could not add a room (availability or inventory gap)
- No "Mark all as read" button present (test 16_2 skips gracefully when button absent)
- Admin-only flows not reachable with Alice/Bob accounts

## Recommendations for Cycle 2
1. After fix agent addresses `test_16_3` and `test_21`, re-run the full suite to verify resolution.
2. The Stripe test_bugs should be flagged to the user for test redesign before cycle 3.
3. Consider investigating why 7 tests are skipped — if skips are masking real failures, they should be reclassified.
