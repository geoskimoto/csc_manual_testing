# Loop Complete — Cycle 1

All 1 cycle complete. Zero real_bug failures remain.

Passed: 63 | Failed: 2 (test_bugs only) | Skipped: 7 (missing_data)

Final report: reports/report.html

---

## What Passed That Was Previously Broken

All three real bugs documented in CLAUDE.md are now fixed:

- **test_17_4_add_funds_entry_point** — Add Funds UI is now present on the wallet page
- **test_19_2_member_cannot_access_admin[/billing/admin-tool/]** — Now returns 403 (not 500) for regular members
- **test_21_responsive_dashboard[phone-viewport0]** — Dashboard no longer overflows at 375px

## Remaining Issues (Not Application Bugs)

### Test Bugs (2 failures — locator needs update, do not change app code)

**tests/test_07_09_payment.py::test_8_1_stripe_success_payment**
**tests/test_07_09_payment.py::test_8_2_stripe_declined_card**

Stripe Link now injects a second iframe into `#card-number-element`. The test helper `_fill_stripe_fields()` uses an ambiguous locator that resolves to both iframes, triggering Playwright strict mode.

Recommended fix in test code (do not touch app):
```python
# Change:
card_frame = page.frame_locator("#card-number-element iframe")
# To:
card_frame = page.frame_locator("#card-number-element iframe[title*='card number']")
# or:
card_frame = page.frame_locator("#card-number-element iframe").first
```

### Missing Data Skips (7 skips)

- **Sections 10, 11** (6 skips): Booking detail link selector `a[href*='/dashboard/booking_detail/']` finds no links on `/dashboard/bookings/` even though seed data created Alice's bookings. The actual URL pattern for booking detail pages likely differs. DOM inspection needed.

- **Section 16** (1 skip): `test_16_4_individual_notification_mark_read` — the notifications page only exposes bulk "Mark All Read", not per-item mark-read links. Either the UI doesn't have this feature or the test selector is wrong.

---

## Recommended Next Steps

1. Update CLAUDE.md to remove the three previously known real bugs from "Known Real Findings"
2. Fix the Stripe iframe locator in `tests/test_07_09_payment.py::_fill_stripe_fields()` (test maintenance, not an app bug)
3. Inspect `/dashboard/bookings/` DOM to find the correct booking detail link selector
4. Inspect `/dashboard/notifications/` to verify per-notification mark-read UI presence
5. Proceed with writing tests for unwritten sections: 2, 5, 6, 12, 13, 15, 22, 23
