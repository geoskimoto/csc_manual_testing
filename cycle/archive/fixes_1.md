# Cycle 1 — Fix Summary

## Fixed

- **test_16_3_mark_all_read_action**: Removed the navbar dropdown's duplicate "Mark all read"
  `<a>` element on DOMContentLoaded in `notifications/list.html`. The Playwright locator
  `"a, button".filter(has_text="Mark all")` was finding the hidden navbar dropdown link first
  (DOM order: navbar renders before page content), preventing the click. Removing the
  duplicate on the notifications page leaves only the visible page-level `<button>` for the
  locator to find.
  - Files: `notifications/templates/notifications/list.html`
  - Commit: a6ed73a

- **test_21_responsive_dashboard[phone-viewport0]**: Removed an extra `</div>` in
  `user_dashboard/templates/user_dashboard/dashboard.html` that was prematurely closing the
  base template's `container-fluid` wrapper. This caused malformed DOM structure (51 opens,
  52 closes outside comments) which triggered horizontal overflow at 375px. Confirmed balanced
  div count after fix (51/51).
  - Files: `user_dashboard/templates/user_dashboard/dashboard.html`
  - Commit: a6ed73a

## Could Not Fix

- **test_8_1_stripe_success_payment** (test_bug): Stripe Elements renders card number, expiry,
  and CVC in separate iframes; test targets only the first iframe for all three fields. Test
  redesign required — do not touch test file.
- **test_8_2_stripe_declined_card** (test_bug): Same root cause as test_8_1.

## Service Status

RUNNING — `csc-booking-test.service` active after restart (2026-05-05 01:32:45 UTC)
