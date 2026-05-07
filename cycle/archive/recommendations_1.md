# Cycle 1 — Recommendations for Next Planner

## Areas likely to have regressed (re-test these)

- Notifications page (mark all read, individual mark read, badge counts)
- Dashboard page at all viewport sizes (phone 375px, tablet 768px, desktop)
- Any page using `dashboard_base.html` — the fixed div structure affects all dashboard pages

## Suggested next test focus

1. **Stripe payment flow** — tests 8_1 and 8_2 are test_bugs requiring redesign (separate
   iframes per field). Priority: human review to decide on Playwright strategy for Stripe Elements.
2. **Booking flow end-to-end** (non-Stripe paths) — wallet-only and admin booking paths not
   yet verified by Playwright suite.
3. **Dashboard responsive layout** — re-verify phone and tablet after the div fix; also test
   other dashboard sub-pages (bookings, wallet, profile) at mobile widths.
4. **Notifications full flow** — mark individual read, dismiss, badge count decrement.
5. **Admin tools** — subscription management, invoice management, booking admin pages.

## Blockers requiring human action

- **Stripe iframe test redesign** (tests 8_1, 8_2): Playwright needs per-field iframe locators
  for Stripe Elements. The test files are locked — a human must redesign the tests before these
  can pass.
- **`run_task.sh` root permission issue**: The `--dangerously-skip-permissions` flag is blocked
  when running as root. The fix agent had to run inline in the main Claude Code session.
  For future automated cycles, either run `run_task.sh` as a non-root user (e.g., `sudo -u
  geoskimoto ...`) or add a workaround to `run_task.sh`.
