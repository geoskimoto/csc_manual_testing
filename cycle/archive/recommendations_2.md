# Cycle 2 — Recommendations for Next Planner

## Areas Likely to Have Regressed (Re-test These)

- Notifications page `mark all read` action — Cycle 1 fix did not resolve; Cycle 2 fix agent
  will attempt a deeper investigation. Re-run `test_16_3` after fix.
- Dashboard at 375px phone viewport — Cycle 1 fix did not resolve; Cycle 2 fix agent will
  identify the specific overflowing element. Re-run `test_21_responsive_dashboard[phone-viewport0]`.

## Suggested Next Test Focus

1. **Verify Cycle 2 fixes** — Re-run `tests/test_16_notifications.py` and
   `tests/test_21_responsive.py` after fix agent completes. These are the only open real_bug items.
2. **Stripe payment test redesign** — `test_8_1` and `test_8_2` remain test_bugs. Human must
   decide whether to redesign these tests to use per-field iframe locators before Cycle 3 can
   close them.
3. **Expand coverage** — If both real_bugs are resolved in Cycle 2, consider adding new test
   sections (cancellation/refund flows, admin booking, subscription management) in Cycle 3.
4. **Booking history with seeded data** — `test_11_2` through `test_11_4` are skipped because
   no completed bookings exist. Seeding or adding a completed-booking fixture would unlock these.

## Blockers Requiring Human Action

- **`seed_test_data` permission gap**: The planner cannot run `seed_test_data` without a
  password-free sudo rule for the `cscbooking` user. Add a NOPASSWD rule:
  ```
  geoskimoto ALL=(cscbooking) NOPASSWD: /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data
  ```
- **Stripe iframe test redesign** (`test_8_1`, `test_8_2`): Requires human to redesign test
  strategy (per-field iframe locators). Test files are locked — cannot be modified by fix agent.
- **`run_task.sh` root permission issue**: Same as Cycle 1 — automated trigger needs to run
  as non-root user for `--dangerously-skip-permissions` to work.

## Stall Watch

Both real_bug failures have now appeared in 2 consecutive cycles. If they appear unchanged in
Cycle 3 as well, the loop will stall. The Cycle 2 fix agent has been given stronger guidance
to look past the Cycle 1 fix and diagnose the true root cause. If Cycle 3 still shows the same
failures, flag for human escalation.
