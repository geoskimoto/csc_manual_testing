# Cycle 2 — Plan and Results

## Focus This Cycle

Based on `cycle/recommendations_1.md`, the priority was to verify whether Cycle 1 fixes resolved the
two real_bug failures. Full suite was run (all 72 tests).

**Test sections run:** All existing sections (01, 03, 04, 07-09, 10, 11, 14, 16, 17, 19, 20, 21).

## Results Summary

| Outcome | Count |
|---------|-------|
| Passed  | 61    |
| Failed  | 4     |
| Skipped | 7     |
| Total   | 72    |

## Failure Classifications

### real_bug (2)

**test_16_3_mark_all_read_action**
- Cycle 1 fix (commit a6ed73a) did not resolve this failure.
- The "Mark all read" `<a>` element is found by Playwright but reported as NOT VISIBLE.
- The locator resolves to `<a href="#" onclick="markAllRead(); return false;" class="btn btn-sm
  btn-link text-decoration-none">Mark all read</a>` — element is not visible.
- The Cycle 1 fix removed what it described as a navbar dropdown duplicate, but the surviving
  element is still hidden. Root cause is not yet resolved.

**test_21_responsive_dashboard[phone-viewport0]**
- Cycle 1 fix (commit a6ed73a) did not resolve this failure.
- Dashboard still has `scrollWidth > clientWidth` at 375px viewport.
- The Cycle 1 fix removed an extra `</div>` tag but the underlying CSS overflow cause was
  not identified or corrected.

### test_bug (2)

**test_8_1_stripe_success_payment / test_8_2_stripe_declined_card**
- Unchanged from Cycle 1. Stripe Elements renders per-field iframes; test targets only first
  iframe for all three fields. Blocked on human redesign of test strategy.

### missing_data (0)

None new.

## Reasoning

- Both real_bug failures carry from Cycle 1 — classified as `real_bug` because the site
  behavior is wrong (hidden button, mobile overflow), not the test.
- Stripe failures remain `test_bug` — the site's Stripe integration is correct; the test
  iframe strategy is wrong.
- No skipped tests changed status vs. Cycle 1.

## Pre-flight Note

`seed_test_data` could not be run (no NOPASSWD sudo for cscbooking user). Cycle 1 seed data
should still be in place; all tests that require seeded data continued to pass (17.x wallet
tests, 16.x notification tests). This is a known operational gap — see recommendations.
