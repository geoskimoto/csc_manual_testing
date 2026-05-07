# Cycle 3 — Recommendations for Next Planner

## Areas likely to have regressed (re-test these)

- Dashboard mobile layout: the `min-width: 0` change is minimal and isolated to the mobile media query, so regression risk is low. But confirm it still renders correctly at tablet and desktop widths.
- Other dashboard pages (bookings list, wallet, profile) that extend `dashboard_base.html` should be verified at 375px — they benefit from the same fix.

## Deploy required before re-testing

**Critical**: Cycle 3's only real_bug fix (b022f81) is committed and pushed to GitHub but NOT yet deployed to staging. The planner must wait for the human to deploy before re-running test_21_responsive. The fix is correct — Playwright confirmed the root cause and the 1-line CSS fix directly addresses it.

Human deploy command (run from deployed dir):
```bash
cd /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io
git pull origin main
sudo systemctl restart csc-booking-test.service
```

## Suggested next test focus

1. **test_21_responsive** — re-run immediately after deploy to confirm the phone overflow is resolved
2. **Full suite** — run all passing tests to check for regressions from the CSS change (unlikely but cheap to verify)
3. **Other dashboard pages at mobile**: bookings list, wallet, profile — these extend dashboard_base.html and benefit from the same fix but weren't tested

## Blockers requiring human action

1. **Deploy the fix**: Run `git pull origin main` + service restart in the deployed directory (see above). The NOPASSWD sudo rules don't cover git pull, so this must be done manually by the human or a NOPASSWD rule must be added for a deploy script.
2. **test_8_1/test_8_2 (Stripe)**: Test bugs requiring test redesign — Stripe Elements puts card number, expiry, and CVC in separate iframes; the tests don't handle this. Human must redesign or skip these tests.
3. **Seed data access**: `sudo -u cscbooking` requires a password, blocking seed_test_data management command. Add NOPASSWD entry or run seed manually to unblock skipped tests (cancellation, booking detail, individual notification mark-read).

## Persistent infra recommendation

Add a NOPASSWD sudo rule for a deploy script to unblock future automated deploys:
```
geoskimoto ALL=(ALL) NOPASSWD: /usr/local/bin/csc-deploy.sh
```
Where `csc-deploy.sh` runs `git pull` + service restart in the deployed dir.
