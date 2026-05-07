# Cycle 3 — Fix Summary

## Fixed

- **tests/test_21_responsive.py::test_21_responsive_dashboard[phone-viewport0]**
  - **Root cause identified via Playwright**: `<main class="flex-grow-1 p-3">` was rendering at 391px inside a 375px flex container. The 16px overflow equals exactly one side of Bootstrap's `p-3` (1rem) padding. The cause is flexbox `min-width: auto` default — flex items won't shrink below their minimum content size. At 375px, the content inside main has a min-content-width that, combined with the 32px of horizontal padding, forces main's minimum size to 391px, overflowing the viewport by 16px.
  - **Fix applied**: Added `min-width: 0` to the `main` selector inside the `@media (max-width: 991.98px)` block in `templates/partials/dashboard_base.html`. This overrides `min-width: auto` and allows the flex item to size correctly to fit its 375px container.
  - **Files touched**: `templates/partials/dashboard_base.html`
  - **Commit**: b022f81

## Could Not Fix

- **Deploy blocker — fix not live on staging**: The code is committed and pushed to GitHub (b022f81) but cannot be deployed to the staging server without human intervention. The deployed directory (`/home/cscbooking/htdocs/csc-booking-test.3rdplaces.io`) is owned by `cscbooking` and requires a password for sudo access. NOPASSWD rules only cover `systemctl restart/status`, not `git pull`. The human must run:
  ```bash
  cd /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io
  git pull origin main
  sudo systemctl restart csc-booking-test.service
  ```
  Until this is done, the test will continue to fail even though the fix is correct.

## Service Status

NOT RESTARTED WITH NEW CODE — service restart was attempted but deployed directory still has old code. Fix is in GitHub at commit b022f81.

## Playwright Verification (pre-deploy)

Confirmed root cause by executing JS in browser at 375px:
- Only overflowing element: `MAIN .flex-grow-1 p-3` with right=391px, width=391px
- Parent flex container: width=375px (correct), scrollWidth=391px (child overflow)
- Fix is minimal (1 CSS line) and directly addresses the measured cause
