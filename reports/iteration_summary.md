# CSC Test Suite — Iteration Summary

**Rounds completed:** 1 of 5 (stopped early — results stabilized after Round 1)
**Final results:** 61 passed · 3 failed · 8 skipped

---

## Test code fixes applied

None. All failures and skips were pre-classified as known app bugs or legitimate data gaps. No test code issues were identified in this run.

---

## Confirmed app bugs (not fixed — site issues)

- `tests/test_17_wallet.py::test_17_4_add_funds_entry_point` — Wallet page has no "Add Funds" link or button. The `/wallet/add-funds/` URL exists but is not surfaced from the wallet page UI.
- `tests/test_19_security.py::test_19_2_member_cannot_access_admin[/billing/admin-tool/]` — `/billing/admin-tool/` returns HTTP 500 for regular members instead of 403/404 or a redirect. Indicates an unguarded admin view throwing an unhandled exception.
- `tests/test_21_responsive.py::test_21_responsive_dashboard[phone-viewport0]` — Dashboard has horizontal overflow at 375px viewport width; layout element is wider than the phone screen.

---

## Legitimate skips (missing test data)

- `tests/test_10_cancellation.py::test_10_1_cancel_button_visible_on_booking` — Alice has no bookings in history; cancellation UI is untestable. **To un-skip:** leave a completed booking in Alice's account.
- `tests/test_10_cancellation.py::test_10_2_refund_url_exists` — Same: no bookings available for Alice.
- `tests/test_10_cancellation.py::test_10_4_cancellation_policy_info_present` — Same: no bookings to open a detail page.
- `tests/test_11_booking_history.py::test_11_2_booking_detail_loads` — Alice has no bookings to click through.
- `tests/test_11_booking_history.py::test_11_3_booking_detail_has_dates_and_room` — Same: no bookings.
- `tests/test_11_booking_history.py::test_11_4_booking_invoice_link` — Same: no bookings.
- `tests/test_16_notifications.py::test_16_3_mark_all_read_action` — No unread notifications present for Alice at test time. **To un-skip:** trigger a booking or system event that generates a notification.
- `tests/test_16_notifications.py::test_16_4_individual_notification_mark_read` — No individual unread notifications with mark-read links present.
