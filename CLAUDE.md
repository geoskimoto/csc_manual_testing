# CSC Manual Testing — Project Context

## What This Project Is

Automated Playwright test suite that replaces the human manual testing guide (`HUMAN_TESTER_GUIDE.md`) for the **Cascade Ski Club (CSC) booking system** running at `https://csc-booking-test.3rdplaces.io/` (staging).

The booking system is a Django app deployed on a Hostinger VPS. It handles lodge room bookings, wallet payments, Stripe payments, membership subscriptions, and family member management for a members-only ski club.

---

## Workflow — How This System Works

1. **Seed test data** — ALWAYS run this before each test suite run (see below)
2. **Run tests:** `./run_tests.sh` — seeds test data, runs the full pytest suite, pipes results through `tester_prompt.md` to a Claude analysis agent, writes `reports/analysis_YYYY-MM-DD.md`.
3. **Read the report:** Review `reports/analysis_YYYY-MM-DD.md` for classified failures (`real_bug`, `test_bug`, `missing_data`) and recommendations.
4. **Hand off to fix agent:** Send the report to a separate Claude agent pointed at `../csc-booking-system-test` for implementation. This session (the tester) does not fix bugs — it only classifies them.

The analysis agent instructions live in `tester_prompt.md` — edit that file to update classification rules or report format without touching the script.

---

## CRITICAL: Seed Before Every Test Run

**Always run `seed_test_data` before each full test suite run.** Tests 2.12–2.14 consume the registration invitation tokens (solo, spouse, child). Once consumed, those tokens are marked `used=True` in the database and the view redirects to sign-in instead of showing the registration form — causing 30-second timeouts.

```bash
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data
```

This is idempotent. It:
- Resets Alice/Bob wallets to $8,000 and ensures active subscriptions
- Ensures seeded confirmed bookings exist (required by tests 10, 11, 28)
- Issues **fresh invitation tokens** for the registration tests, written to `/tmp/csc_reg_test_tokens.json`
- Ensures StuckPayment fixtures exist for test_24

The cleanup step in `seed_test_data` nullifies invoices against reg-test profiles before deleting them. This handles the case where test_26 (invoice admin) created test invoices against a previously-registered test user — `Invoice.customer` is `PROTECT`, so the invoices must be detached before the profile can be deleted.

---

## Key Files

| File | Purpose |
|------|---------|
| `HUMAN_TESTER_GUIDE.md` | The source of truth for what to test — 29 sections covering every flow |
| `URL_REFERENCE.md` | All app URLs mapped to their Django named routes |
| `credentials.txt` | Test accounts — Alice, Bob, booking_admin, financial_admin |
| `run_tests.sh` | Primary entry point — seeds, tests, and analyzes in one command |
| `tester_prompt.md` | Instructions given to the Claude analysis agent after each run |
| `tests/helpers.py` | Shared constants: BASE_URL, all page URLs, credentials, login helper |
| `tests/conftest.py` | Pytest fixtures: `page`, `alice_page`, `bob_page`, `booking_admin_page`, `financial_admin_page` |
| `pytest.ini` | Runs with `--html=reports/report.html` and `--json-report-file=reports/report.json` |
| `reports/` | Generated after each run — HTML report for human review, JSON for CI |
| `tests/screenshots/` | PNG captured on every test for visual evidence |

---

## Test Accounts

| Account | Email | Password | Role |
|---------|-------|----------|------|
| Alice | `alice.tester@csc-test.local` | `TestPass99!` | Regular member, $8,000 wallet, subscription active to 2027 |
| Bob | `bob.tester@csc-test.local` | `TestPass99!` | Same setup as Alice |
| Booking Admin | `booking.admin@csc-test.local` | `AdminPass99!` | Booking + financial admin tools, no `/admin/` |
| Financial Admin | `financial.admin@csc-test.local` | `AdminPass99!` | All booking admin access + `/admin/` |
| Members+ | `members.plus@csc-test.local` | `AdminPass99!` | Regular member + newsletter management only (`can_manage_newsletters`), no `/admin/`, no booking-admin tools |

Registration test accounts (created/consumed per run by seed_test_data):

| Label | Email |
|-------|-------|
| validation | `reg.validation@csc-test.local` |
| solo | `reg.solo@csc-test.local` |
| spouse | `reg.spouse@csc-test.local` |
| child | `reg.child@csc-test.local` |

---

## Critical URL Corrections (Learned from Discovery)

The site uses non-standard URL patterns — do not guess. Always consult `URL_REFERENCE.md`.

| What | Correct URL |
|------|-------------|
| Login | `/user/sign-in/` |
| Availability | `/bookings/check_availability/` |
| Cart | `/bookings/view_booking_cart/` |
| Add to cart | `/bookings/add_accommodations_to_cart/` |
| Checkout | `/bookings/checkout/` |
| Dashboard | `/dashboard/` |
| Profile | `/dashboard/profile/` |
| Wallet | `/dashboard/wallet/` |
| Admin bookings | `/admin-bookings/` |
| Manage bookings | `/admin-bookings/manage-bookings/` |
| Transactions | `/admin-bookings/transactions/` |
| Invoice admin | `/billing/admin-tool/` |
| Subscription admin | `/subscriptions/admin/list/` |
| Stuck payments | `/bookings/admin/stuck-payment-dashboard/` |

Login form fields: `name="email"` and `name="password"` (not `name="login"`).

---

## Access Control Behavior

**Important:** Django's `PermissionDenied` exception always returns a **403 response** — the URL does NOT change. It does NOT redirect to login. This affects all "member blocked" test assertions:

```python
resp = await alice_page.goto(URL)
status = resp.status if resp else 0
url = alice_page.url
is_blocked = status in (403, 404) or "sign-in" in url or "login" in url or "403" in url
assert is_blocked
```

Do not assert `"sign-in" in url` alone — that will fail for 403 responses (URL stays on the original page).

Key decorators/mixins and their behavior:
- `@financial_administrator_required` — raises PermissionDenied (403) for all non-FA users, including anonymous. No login redirect.
- `BookingAdminRequiredMixin` — grants access to both Booking Admins and Financial Admins. Raises 403 for members and anonymous users.

---

## Test Coverage Status

_258 tests collected as of 2026-08-03; 264 as of 2026-09-28 with sections 37-42 added. A full re-run on 2026-09-28 (the suite's first run since 2026-08-03) surfaced 6 tests that had gone stale against real app changes in the intervening ~8 weeks — all fixed same day except the two noted below. See "Known Issues" for the two still open. Re-verify this section's counts whenever the suite goes this long between runs; staleness compounds with wall-clock time, not just code changes (see the seed-fixture date-drift issue below)._

| Section | File | Tests | Status |
|---------|------|-------|--------|
| 1 — Environment / Login | `test_01_environment.py` | 4 | Passing |
| 2 — Registration / Onboarding | `test_02_registration.py` | 16 | Passing — **tokens consumed each run; seed required** |
| 3 — Dashboard | `test_03_dashboard.py` | 5 | Passing |
| 4 — Booking (Individual) | `test_04_booking_individual.py` | 6 | Passing |
| 5 — Family Booking | `test_05_family_booking.py` | 5 | Passing |
| 6 — Guest Booking | `test_06_guest_booking.py` | 4 | Passing |
| 7–9 — Payments | `test_07_09_payment.py` | 5 | Passing |
| 10 — Cancellation/Refund | `test_10_cancellation.py` | 4 | 1 skip — cancellation policy text not visible for seeded state |
| 11 — Booking History | `test_11_booking_history.py` | 5 | Passing |
| 12 — Admin Booking | `test_12_admin_booking.py` | 8 | Passing |
| 13 — Admin Manage | `test_13_admin_manage.py` | 6 | Passing |
| 14 — Subscriptions | `test_14_subscriptions.py` | 6 | Passing |
| 15 — Invoicing | `test_15_invoicing.py` | 7 | Passing |
| 16 — Notifications | `test_16_notifications.py` | 6 | 1 skip — no per-notification mark-read link in current UI |
| 17 — Wallet Operations | `test_17_wallet.py` | 8 | Passing |
| 18 — Profile/Family Mgmt | `test_18_profile.py` | 8 | Passing |
| 19 — Security | `test_19_security.py` | 4 | Passing |
| 20 — Edge Cases | `test_20_edge_cases.py` | 3 | Passing |
| 21 — Responsive | `test_21_responsive.py` | 2 | Passing |
| 22 — Cross-Browser | `test_22_cross_browser.py` | 5 | Skips gracefully if Firefox/WebKit not installed |
| 23 — Race Conditions | `test_23_race_conditions.py` | 3 | Passing |
| 24 — Stuck Payments Dashboard | `test_24_stuck_payments.py` | 9 | Financial Admin only (login-redirect for anonymous since the app's 2026-09-23 `deny_access()` change, 403 for authenticated-but-unauthorized). 1 open issue — see Known Issues (`test_24_8`) |
| 25 — Admin Transactions Filters | `test_25_admin_transactions_filters.py` | 9 | Passing |
| 26 — Invoice Admin | `test_26_invoice_admin.py` | 9 | Passing — creates test invoices; seed cleans them up. `test_26_8` fixed 2026-09-28 (`payment_method` field renamed to `offline_method`) |
| 27 — Subscription Admin | `test_27_subscription_admin.py` | 8 | Passing |
| 28 — Admin Refund Modal | `test_28_admin_refund.py` | 8 | Passing — does NOT submit refund (protects Alice's seeded booking) |
| 29 — Lodge Map Booking | `test_29_lodge_map.py` | 16 | 1 known real app bug (test_29_5 — see Known Issues). 29_13/29_14 skip if multi-member or guest options absent (missing_data) |
| 30 — Bed List Map | `test_30_bed_list_map.py` | 8 | Passing |
| 31 — Club Events | `test_31_club_events.py` | 8 | Passing |
| 32 — Membership Subscription Workflow | `test_32_membership_subscription.py` | 12 | Passing — skips (32_6, 32_7, 32_8) when Bob already has an active/pending subscription (run 32.5 first). `test_32_7` fixed 2026-09-28 to skip like 32_8 instead of hard-failing when 32_6 skips |
| 33 — Admin Booking E2E | `test_33_admin_booking_e2e.py` | 6 | Passing |
| 34 — Members+ Role & Newsletter Mgmt | `test_34_newsletters.py` | 8 | Passing — requires `members.plus@csc-test.local` + seeded Newsletter fixture. `test_34_8` fixed 2026-09-28 — asserts the specific expected item set (6, not 1) now that Members+ has more capabilities |
| 35 — Admin Alert Recipients | `test_35_admin_alerts.py` | 7 | Passing — requires seeded `AdminAlertRecipient` (stuck_payment) fixture |
| 36 — Financial Dashboard / AR Aging / Deferred Revenue | `test_36_financial_dashboard.py` | 16 | 1 open issue — see Known Issues (`test_36_16`, seed-fixture date drift) |
| 37 — Credit Member Wallet (admin) | `test_37_credit_wallet.py` | 5 | Added 2026-09-28 |
| 38 — Promote-to-Account-Holder | `test_38_promote_account_holder.py` | 5 | Added 2026-09-28 — acceptance-page happy path NOT automated (no way to read the invitation email); see Known Issues |
| 39 — Waivers | `test_39_waivers.py` | 9 | Added 2026-09-28 — never signs the seeded member fixture (would break the compliance-roster fixture). Guest-sign tests (39_3, 39_8, 39_9) discover a live `audience in (guests, both)` template via `guest_sign_links` and **skip** rather than fail when none exists — staging had none as of 2026-09-28, a missing_data gap worth seeding if this coverage matters ongoing |
| 40 — Broadcasts (admin club-wide email) | `test_40_broadcasts.py` | 7 | Added 2026-09-28 — never clicks the real "Send to {N} recipients" button; only "Send test to myself". `test_40_7` skips when the audience is under `BROADCAST_TYPED_CONFIRM_THRESHOLD` (no gate rendered) |
| 41 — Maintenance Reports | `test_41_maintenance_reports.py` | 7 | Added 2026-09-28 — status-update test conditional on a report existing |
| 42 — Profile Integrity admin page | `test_42_profile_integrity.py` | 5 | Added 2026-09-28 — dismiss/undismiss round trip conditional on a live finding existing; expands the `#dismissed-findings` Bootstrap collapse before interacting with it |

---

## Known Issues

### Real App Bugs (do not fix by modifying the test)

- **`test_29_5_room_color_changes_on_assignment`:** Deliberately rewritten (commit `6c0939f`) to use a deterministic `wait_for_function` instead of a fixed sleep, specifically to expose a real bug in the lodge map JS: selecting an occupant in the popover does not reliably flip the room's `data-state` to `assigned` within 5s. Confirmed still failing as of 2026-08-03, and again 2026-09-28. Leave the test as-is — it is correctly failing against real app behavior, not a stale assertion.

### Open — needs investigation or a fix in the other repo

- **`test_36_16_seeded_overdue_invoice_visible_in_31_60_bucket`** (found 2026-09-28, not yet fixed): the seed fixture for Alice's overdue invoice (created by `seed_financial_test_data` / `seed_test_data` in `csc-booking-system-test`) uses a **fixed calendar due date** (June 19, 2026) rather than one computed relative to "today." It was ~45 days overdue (31-60 bucket) when this test was written on 2026-08-03; by 2026-09-28 it's ~101 days overdue (90+ bucket), and by the time anyone reads this it may have drifted further. This is a bug in the main app's seed command, not in this test — fix there (compute the due date as `date.today() - timedelta(days=45)` at seed time, not a literal date) rather than loosening this assertion.
- **`test_24_8_unresolved_record_visible`** (found 2026-09-28, not yet fixed): the seeded unresolved `StuckPayment` fixture (`pi_seed_test_unresolved`) wasn't present when this ran on 2026-09-28 — the dashboard showed 0 unresolved. Suspected but unconfirmed cause: the real `csc-retry-stuck-payments.timer` (runs every 15 minutes on staging per the main repo's `CLAUDE.md`) may process and resolve the fake seeded payment intent before this test gets to it, if enough wall-clock time passes between `seed_test_data` and running this section. Needs someone to check `retry_stuck_payments`'s behavior against a payment intent ID that doesn't exist in Stripe, and/or seed closer to test time.

### Not Automated (by design)

- **Fiscal-year closing / period-lock protection:** The `financials.period_lock.assert_period_open()` guard (blocks invoice voids/payments/edits dated inside a closed accounting period) is exercised only via a Django-admin bulk action (`/admin/financials/fiscalyear/`, "Close fiscal year(s)"), reachable only by Financial Administrators/superuser. There is no UI route to close a period, and no "reopen" action in this phase — only a superuser manually flipping `is_closed` in the DB. Automating this against shared staging state would permanently close a real accounting period with no clean rollback, so it is intentionally **not** covered by an automated test. If this needs verification, do it manually: create a disposable far-future/past `FiscalYear` (never the real current one), close it via the admin action, attempt a payment/void/edit dated inside it through the app UI, and confirm the `messages.error` text: `"Fiscal year {name} ({start} to {end}) is closed. This date ({date}) falls inside a closed accounting period and cannot be modified."`
- **Promote-to-Account-Holder acceptance flow (`test_38`):** The public token-acceptance page (`/user/promote/<token>/`) can only be reached with a real `ProfilePromotionInvitation` token, which is only ever delivered by email — this suite has no way to read staging's sent mail. `test_38` covers the admin-side send flow and the public page's handling of a bogus token, but not completing a real acceptance. If this needs verification, do it manually: send an invitation to an address you control, open the emailed link, and confirm the account-creation form works and preserves the profile's `pid`/`family`/booking history.

### Permanent / Intentional Skips

- **`test_10_4_cancellation_policy_info_present`:** Cancellation policy text not visible for the seeded booking's state. Needs a booking seeded in a state where policy text renders.
- **`test_16_4_individual_notification_mark_read`:** Notifications UI only exposes bulk "Mark All Read" — no per-notification mark-read link. Product decision needed.
- **Cross-browser tests (test_22):** Skip if Firefox/WebKit binaries are not installed. Run `sudo playwright install firefox webkit && sudo playwright install-deps` to enable.

### Side Effects Between Test Sections

- **test_26 (Invoice Admin)** creates invoices against real customer profiles in the DB. If those customers happen to be previously-registered reg-test users, `seed_test_data` cleanup will fail with `ProtectedError` unless the invoices are detached first. This is handled by the seed command (see `_ensure_registration_tokens`).
- **test_28 (Admin Refund)** intentionally does NOT submit the refund form. Submitting would cancel Alice's seeded future booking and break tests 10, 11.

---

## Selector Patterns and Gotchas

- **Invoice admin action buttons**: Use `a.btn[has_text="Send via Email"]`, `a.btn[has_text="Record Payment"]`, `a.btn[has_text="Void Invoice"]` — scoped to `a.btn` to avoid matching nav dropdown items with similar text (e.g., "Send Invitation").
- **Invoice filter chip "All"**: Use `a.btn[href*='tab=invoices'][has_text='All']` — scoped to avoid matching the navbar "Mark all read" link which also renders as `a.btn`.
- **Select2 customer field**: Use `page.select_option('select[name="customer"]', index=1)` on the underlying `<select>` element to bypass the Select2 overlay.
- **Invoice formset (create)**: The `LineItemFormSet` has `extra=3` empty rows. Before submitting, set `form-TOTAL_FORMS` to `"1"` via `page.evaluate()` to prevent empty-row validation errors.
- **Subscription details modal**: Triggered by `.view-details-btn` via AJAX. Wait for `#subscriptionDetailsModal.show` (not just `#subscriptionDetailsModal`).
- **Admin refund modal**: Triggered by `.refund-booking-btn`. Wait for `#refundBookingModal.show`.
- **Availability page card-view selects**: Map View is the default view on `/bookings/check_availability/` (since app commit `6b0b351`) — `#rooms-content` (card view, where `select.member-select` occupant dropdowns live) starts `d-none`. Call `switch_to_card_view(page)` from `tests/helpers.py` right after searching availability and before touching `select.member-select`.
- **Invoice pay links**: Scope to `a.btn-success[href*="/pay/"]`, never a bare `a[href*="/pay/"]` — the notification-dropdown partial in `navbar.html` (present on every page) renders a matching but hidden link for unread pay-invoice notifications, and an unscoped locator's `.first` can resolve to that instead of the real button.
- **Stripe-mounted pages (checkout, invoice payment)**: Use `wait_for_load_state("load")`, never `"networkidle"`, after navigating to or clicking into a page that mounts a Stripe PaymentElement/iframe — Stripe keeps background network activity alive indefinitely, so `networkidle` never resolves and times out.
- **FullCalendar root element**: FullCalendar applies its `fc` class to the container element you hand it (`document.getElementById(...)`), not to a child — so target it with a compound selector (`#dashboard-club-calendar.fc`), never a descendant combinator (`#dashboard-club-calendar .fc`), which can never match.
- **Date-of-birth fields (SelectDateWidget)**: Since app commit `4cee11a`, every DOB field (family registration, and any new admin form using the same pattern) renders as three separate `<select>` elements, not a single date input — `name="{field}_month"` (values `"1"`–`"12"`, no zero-padding), `name="{field}_day"` (values `"1"`–`"31"`), `name="{field}_year"` (descending from the current year, values are the literal 4-digit year). Use three `select_option()` calls; a `.fill()` against `[name="{field}"]` matches nothing and silently no-ops.
- **`fetch()`-driven admin actions**: Some newer admin tools (e.g. Profile Integrity dismiss/undismiss) act via a `fetch()` call from a button click rather than a form submit. The Profile Integrity page calls `location.reload()` itself once the fetch resolves successfully — wrap the click in `async with page.expect_navigation():` rather than clicking-then-`wait_for_load_state`, since the reload happens asynchronously after the click handler returns. On failure it raises a blocking `alert()` — register a `page.on("dialog", lambda d: d.accept())` handler before clicking, or the test hangs waiting on the dialog.
- **Don't switch the role fixtures to a shared Playwright `storage_state`** (tried and reverted 2026-09-28). It cuts ~250+ real per-test logins down to 5, but every test for a role then shares the exact same Django `sessionid`, and the admin booking cart is session-bound (test_33's own docstring: "every fixture opens a fresh browser context (fresh session)"). That shared session let stale/expired cart state from one test leak into another — surfaced as `test_33_2_admin_creates_wallet_paid_booking` hanging 45s waiting for a checkout redirect that never came, because the cart it POSTed had gone stale between whichever tests shared its session. Fresh per-test logins are a correctness requirement, not just a login-flow nicety.
- **CKEditor5 fields** (e.g. broadcast `body`): a rich-text contenteditable area, not a plain textarea — `.fill()` against `[name="body"]` does nothing. Use `tests/helpers.py::fill_ckeditor(page, field_id, text)`, which sets content through the editor's own `ckeditorInstance.setData()` JS API rather than simulating clicks/typing into the rich-text area.

---

## Running Tests

```bash
# Always seed first, then run
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data

cd /home/geoskimoto/projects/csc_manual_testing
.venv/bin/python -m pytest tests/ -v --tb=short
```

Or use the all-in-one script (seeds + runs + analyzes):

```bash
./run_tests.sh
```

Run a single section manually:

```bash
.venv/bin/pytest tests/test_02_registration.py -v
```

---

## RETIRED — Loop System (historical reference only)

The cycle state machine, handoff files, and fix agent prompt system below are no longer used. `run_tests.sh` replaced the entire loop. The `cycle/` directory is left in place as a historical artifact. **Do not use this system — use `run_tests.sh` instead.**

### Cycle State Machine

All loop state lives in `cycle/state.json`:

```json
{
  "cycle_count": 0,
  "max_cycles": 5,
  "phase": "ready",
  "last_run": null,
  "failure_history": [],
  "stall_count": 0,
  "loop_complete": false
}
```

**Phases:** `ready` → `testing` → `awaiting_fix` → (fix agent runs) → `awaiting_review` → (human approves) → back to `ready`

**At the start of every planner run:**
1. Read `cycle/state.json`
2. If `loop_complete` is true → write `cycle/LOOP_COMPLETE.md`, stop
3. If `cycle_count >= max_cycles` → write `cycle/LOOP_COMPLETE.md`, set `loop_complete: true`, stop
4. Check stall: if the last 3 entries of `failure_history` are identical sets of test IDs → write `cycle/LOOP_STALLED.md`, set `phase: stalled`, stop
5. Increment `cycle_count`, set `phase: testing`, update `last_run`, write back `cycle/state.json`

### Pre-Flight: Seed Test Data

Before running pytest, always seed test data. The staging site runs under the `cscbooking` user with its own PostgreSQL — seed that database, not the geoskimoto dev copy:

```bash
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data
```

This is idempotent. It ensures Alice has bookings, a $8,000 wallet, and an unread notification — prerequisites for sections 10, 11, 16, and 17. It also issues fresh registration tokens consumed by tests 2.12–2.14.

### Running Tests

```bash
.venv/bin/pytest -v --tb=short \
  --json-report --json-report-file=reports/report.json \
  --html=reports/report.html
```

### Failure Classification

After parsing `reports/report.json`, classify each failure. Do NOT fix test code — only classify:

| Class | Meaning | Action |
|---|---|---|
| `real_bug` | The site behavior is wrong — the test is correct | Include in handoff for fix agent |
| `test_bug` | The test assertion is wrong — the site behavior is acceptable | Document, but do NOT modify the test; report to user |
| `missing_data` | Test requires DB state that seed_test_data didn't create | Document the gap; do NOT skip |

### Writing the Handoff File

Write `cycle/handoff_{N}.json` where N is the current `cycle_count`:

```json
{
  "cycle": 1,
  "timestamp": "2026-04-28T13:20:00",
  "summary": {"passed": 61, "failed": 3, "skipped": 8},
  "failures": [
    {
      "test_id": "tests/test_17_wallet.py::test_17_4_add_funds_entry_point",
      "classification": "real_bug",
      "description": "Wallet page has no Add Funds entry point. Test navigates to /dashboard/wallet/ and looks for a link or button to /wallet/add-funds/ — none present.",
      "likely_files": ["wallet/views.py", "templates/wallet/wallet.html", "user_dashboard/templates/"],
      "do_not_touch": ["tests/test_17_wallet.py"]
    }
  ],
  "test_bugs": [],
  "missing_data": [],
  "stop_loop": false
}
```

Set `stop_loop: true` if there are zero `real_bug` failures (loop is done).

### Writing the Fix Agent Prompt

Write `/home/geoskimoto/projects/csc-booking-system-test/loop/csc_fix_cycle_{N}.txt` (absolute path — NOT relative, NOT `.pending` — it is run manually by the human via `nightly_tasks/run_task.sh`). Use this exact header and body template, filling in cycle-specific details:

```
# WORKDIR: /home/geoskimoto/projects/csc-booking-system-test
# MODEL: sonnet
# MAX_TURNS: 100
---
You are the Fix Agent for the CSC booking system automated test loop. Cycle {N}.

Read your operating instructions from CLAUDE.md in this directory before doing anything else.
Then read /home/geoskimoto/projects/csc_manual_testing/cycle/handoff_{N}.json for the failures
to fix this cycle.

Human override note (if any):
{HUMAN_OVERRIDE or "None"}

Fix each `real_bug` failure. When done, write the review package and pending planner prompt
as described in your CLAUDE.md Fix Agent section.
```

### Writing the Cycle Plan

Write `cycle/plan_{N}.md` with:
- Which test sections were run and why (based on prior recommendations)
- Summary of results
- What you chose to classify as real_bug vs test_bug vs missing_data, and why

### After Writing All Outputs

Update `cycle/state.json`: set `phase: awaiting_fix`, append current failure test_ids to `failure_history` (keep last 3 only).

### Completion / Stall

**If zero real_bug failures:**
```markdown
# cycle/LOOP_COMPLETE.md
All {N} cycles complete. Zero real_bug failures remain.
Passed: X | Failed: Y (test_bugs/missing_data only) | Skipped: Z
Final report: reports/report.html
```
Set `loop_complete: true`, `phase: complete` in state.json. Do NOT write a fix prompt.

**If stalled (same failures 3 cycles):**
```markdown
# cycle/LOOP_STALLED.md
Loop stalled after {N} cycles. The following failures did not change:
- test_id_1
- test_id_2
These likely require manual investigation or missing test accounts.
```
Set `phase: stalled`. Do NOT write a fix prompt.

---

## Tech Stack

- Python 3.12, pytest, pytest-asyncio, playwright (Chromium headless)
- `pytest-html` for HTML reports, `pytest-json-report` for JSON
- Django backend (the app under test) — PostgreSQL, Stripe test mode
