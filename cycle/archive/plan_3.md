# Cycle 3 — Plan and Results

## Context

This is the first post-deployment verification run. Cycles 1 and 2 identified two `real_bug` failures; fixes were applied in commit `a6ed73a` and staging was redeployed before this cycle ran.

## Test Sections Run

All currently written test sections were run (72 tests collected):

| File | Section | Tests |
|------|---------|-------|
| test_01_environment.py | 1 — Login/Environment | 4 |
| test_03_dashboard.py | 3 — Dashboard | 5 |
| test_04_booking_individual.py | 4 — Individual Booking | 6 |
| test_07_09_payment.py | 7–9 — Payments | 5 |
| test_10_cancellation.py | 10 — Cancellation | 4 |
| test_11_booking_history.py | 11 — Booking History | 5 |
| test_14_subscriptions.py | 14 — Subscriptions | 6 |
| test_16_notifications.py | 16 — Notifications | 6 |
| test_17_wallet.py | 17 — Wallet | 8 |
| test_18_profile.py | 18 — Profile/Family Mgmt | 8 |
| test_19_security.py | 19 — Security | 7 |
| test_20_edge_cases.py | 20 — Edge Cases | 3 |
| test_21_responsive.py | 21 — Responsive | 5 |

## Results

**3 failed, 62 passed, 7 skipped** (352.93s)

## Deployment Verification: What Changed

The deployment (commit a6ed73a) fixed **three** previously failing tests:

1. `test_16_3_mark_all_read_action` — Mark All Read button on notifications page is now visible and clickable. **VERIFIED FIXED.**
2. `test_17_4_add_funds_entry_point` — Add Funds entry point now present on wallet page. **VERIFIED FIXED.**
3. `test_19_2_member_cannot_access_admin[/billing/admin-tool/]` — Now returns 403 instead of 500. **VERIFIED FIXED.**

## Failure Classifications

### real_bug (1)

**`test_21_responsive_dashboard[phone-viewport0]`** — Dashboard horizontal overflow at 375px persists for the third consecutive cycle. Prior fix (removing a `</div>`) addressed template structure but not the actual CSS/layout cause of the overflow. This requires identifying the specific overflowing element via width measurement in the browser.

Classification rationale: The test is correct — a club booking site should not overflow at 375px (standard iPhone width). The site behavior is wrong.

### test_bug (2)

**`test_8_1_stripe_success_payment`** and **`test_8_2_stripe_declined_card`** — Stripe Elements renders three separate iframes; the tests attempt to fill the expiry field inside the card number iframe, where it does not exist. The test logic is wrong (not the site). These require redesign to target per-field iframes and are blocked on human review.

Classification rationale: The site correctly renders Stripe Elements. The test's iframe locator strategy is incorrect.

## Stall Check

- Cycle 1 real_bugs: `[test_16_3_mark_all_read_action, test_21_responsive_dashboard]`
- Cycle 2 real_bugs: `[test_16_3_mark_all_read_action, test_21_responsive_dashboard]`
- Cycle 3 real_bugs: `[test_21_responsive_dashboard]`

Not all three identical. **No stall.**

## Seed Data Blocker

`seed_test_data` could not be run — `sudo -u cscbooking` requires a password and NOPASSWD is not configured. 7 tests remained skipped (cancellation detail, booking detail, individual notification mark-read). These skips are pre-existing and not a regression.

## Recommendations for Cycle 4

1. **Dashboard phone overflow** — Fix agent must use Playwright to find elements with `offsetWidth > 375` on the dashboard at 375px. Likely a table, card, or flex row with a fixed min-width. Apply CSS fix (`max-width: 100%`, `overflow-x: hidden`, or responsive breakpoint) and redeploy.
2. **Stripe test redesign** — Human action required. The test files are locked; a human must redesign tests 8_1 and 8_2 to use per-field iframe locators.
3. **Seed data sudoers** — Add NOPASSWD entry for the seed_test_data management command so skipped tests can run.
4. **New test sections to add** — Guest booking (section 6), admin tools (sections 12–13, requires admin credentials), financial admin (section 15), cross-browser (section 22).
