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

_173 tests collected as of 2026-05-08. Last full run: 164 passed / 3 failed (seed issue, now fixed) / 6 skipped._

| Section | File | Tests | Status |
|---------|------|-------|--------|
| 1 — Environment / Login | `test_01_environment.py` | 4 | Passing |
| 2 — Registration / Onboarding | `test_02_registration.py` | 16 | Passing — **tokens consumed each run; seed required** |
| 3 — Dashboard | `test_03_dashboard.py` | 5 | Passing |
| 4 — Booking (Individual) | `test_04_booking_individual.py` | 6 | Passing |
| 5 — Family Booking | `test_05_family_booking.py` | 5 | Written |
| 6 — Guest Booking | `test_06_guest_booking.py` | 4 | Written |
| 7–9 — Payments | `test_07_09_payment.py` | 5 | 2 test bugs in Stripe iframe locator (see Known Issues) |
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
| 24 — Stuck Payments Dashboard | `test_24_stuck_payments.py` | 9 | Passing — Financial Admin only (403 for all others) |
| 25 — Admin Transactions Filters | `test_25_admin_transactions_filters.py` | 9 | Passing |
| 26 — Invoice Admin | `test_26_invoice_admin.py` | 9 | Passing — creates test invoices; seed cleans them up |
| 27 — Subscription Admin | `test_27_subscription_admin.py` | 8 | Passing |
| 28 — Admin Refund Modal | `test_28_admin_refund.py` | 8 | Passing — does NOT submit refund (protects Alice's seeded booking) |
| 29 — Financial Dashboard | not written | — | Not planned |

---

## Known Issues

### Test Bugs (test needs updating, not the app)

- **`test_8_1_stripe_success_payment`, `test_8_2_stripe_declined_card`:** `_fill_stripe_fields()` uses `locator("input")` which resolves to 6 elements inside the Stripe iframe (strict mode violation). Fix: use `card_frame.get_by_role("textbox", name="Credit or debit card number")` for card number, and equivalent targeted selectors for expiry/CVV.

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
