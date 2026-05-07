# CSC Manual Testing — Project Context

## What This Project Is

Automated Playwright test suite that replaces the human manual testing guide (`HUMAN_TESTER_GUIDE.md`) for the **Cascade Ski Club (CSC) booking system** running at `https://csc-booking-test.3rdplaces.io/` (staging).

The booking system is a Django app deployed on a Hostinger VPS. It handles lodge room bookings, wallet payments, Stripe payments, membership subscriptions, and family member management for a members-only ski club.

---

## Workflow — How This System Works

1. **Run tests:** `./run_tests.sh` — seeds test data, runs the full pytest suite, pipes results through `tester_prompt.md` to a Claude analysis agent, writes `reports/analysis_YYYY-MM-DD.md`.
2. **Read the report:** Review `reports/analysis_YYYY-MM-DD.md` for classified failures (`real_bug`, `test_bug`, `missing_data`) and recommendations.
3. **Hand off to fix agent:** Send the report to a separate Claude agent pointed at `../csc-booking-system-test` for implementation. This session (the tester) does not fix bugs — it only classifies them.

The analysis agent instructions live in `tester_prompt.md` — edit that file to update classification rules or report format without touching the script.

---

## Key Files

| File | Purpose |
|------|---------|
| `HUMAN_TESTER_GUIDE.md` | The source of truth for what to test — 23 sections covering every flow |
| `URL_REFERENCE.md` | All app URLs mapped to their Django named routes |
| `credentials.txt` | Test accounts (Alice and Bob) — both Regular members, $8000 wallet balance |
| `run_tests.sh` | Primary entry point — seeds, tests, and analyzes in one command |
| `tester_prompt.md` | Instructions given to the Claude analysis agent after each run |
| `tests/helpers.py` | Shared constants: BASE_URL, all page URLs, credentials, login helper |
| `tests/conftest.py` | Pytest fixtures: `browser`, `page`, `alice_page`, `bob_page` |
| `pytest.ini` | Runs with `--html=reports/report.html` and `--json-report-file=reports/report.json` |
| `reports/` | Generated after each run — HTML report for human review, JSON for CI |
| `tests/screenshots/` | PNG captured on every test for visual evidence |

---

## Test Accounts

- **Alice** `alice.tester@csc-test.local` / `TestPass99!` — Regular member, wallet $8000, subscription active to 2027-04-19
- **Bob** `bob.tester@csc-test.local` / `TestPass99!` — Same setup as Alice

**Missing accounts needed for full test coverage:**
- Admin/booking administrator account (needed for Tests 12.x, 13.x, 23.x)
- Financial administrator account (needed for Tests 15.x)
- Member without active subscription (needed for Test 14.2, 20.9)

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

Login form fields: `name="email"` and `name="password"` (not `name="login"`).

---

## Test Coverage Status

_Last updated from `reports/analysis_2026-05-05.md`: 68 passed / 2 failed (test bugs) / 2 skipped / 72 total_

| Section | Tests Written | Status |
|---------|--------------|--------|
| 1 — Environment / Login | `test_01_environment.py` | Passing |
| 3 — Dashboard | `test_03_dashboard.py` | Passing |
| 4 — Booking (Individual) | `test_04_booking_individual.py` | Passing |
| 7–9 — Payments | `test_07_09_payment.py` | 2 test bugs in Stripe iframe locator (see Known Issues) |
| 10 — Cancellation/Refund | `test_10_cancellation.py` | 1 skip — cancellation policy text not visible for seeded booking state |
| 11 — Booking History | `test_11_booking_history.py` | Written |
| 14 — Subscriptions | `test_14_subscriptions.py` | Written |
| 16 — Notifications | `test_16_notifications.py` | 1 skip — no per-notification mark-read link in current UI |
| 17 — Wallet Operations | `test_17_wallet.py` | Passing |
| 18 — Profile/Family Mgmt | `test_18_profile.py` | Written |
| 19 — Security | `test_19_security.py` | Passing |
| 20 — Edge Cases | `test_20_edge_cases.py` | Passing |
| 21 — Responsive | `test_21_responsive.py` | Passing |
| 2 — Registration / Onboarding | Not yet written | |
| 5 — Family Booking | Not yet written | Needs family member test data |
| 6 — Guest Booking | Not yet written | |
| 12 — Admin Booking | Not yet written | Needs admin credentials |
| 13 — Admin Manage | Not yet written | Needs admin credentials |
| 15 — Invoicing | Not yet written | Needs financial admin credentials |
| 22 — Cross-Browser | Not yet written | Requires `playwright install firefox webkit` |
| 23 — Race Conditions | Partial (Test 20.6) | Needs precise timing; some require Django shell access |

---

## Known Issues

### Test Bugs (test needs updating, not the app)

- **`test_8_1_stripe_success_payment`, `test_8_2_stripe_declined_card`:** `_fill_stripe_fields()` uses `locator("input")` which resolves to 6 elements inside the Stripe iframe (strict mode violation). Fix: use `card_frame.get_by_role("textbox", name="Credit or debit card number")` for card number, and equivalent targeted selectors for expiry/CVV.

### Missing Data / Skips

- **`test_10_4_cancellation_policy_info_present`:** Cancellation policy text not visible for the seeded booking's state. Needs a booking seeded in a state where policy text renders.
- **`test_16_4_individual_notification_mark_read`:** Notifications UI only exposes bulk "Mark All Read" — no per-notification mark-read link present. Product decision needed: missing feature or acceptable behavior?

### Previously Fixed (no longer tracked)

- Phone layout overflow at 375px — fixed
- `/billing/admin-tool/` returning 500 instead of 403 — fixed
- Wallet page missing Add Funds UI link — fixed

---

## What's Needed to Complete the Suite

1. **Admin credentials** — add to `credentials.txt` and `helpers.py` for Tests 12–13, 15
2. **No-subscription member account** — for Tests 14.2, 20.9
3. **Availability form field names** — need to inspect `/bookings/check_availability/` page DOM to find date input field names and submit button selector (likely a JS-rendered date picker, not a plain `<input type="date">`)
4. **Cart pre-fill helper** — a reusable fixture that logs in, searches availability, adds a room to cart, so payment tests (7–9) can run end-to-end
5. **Firefox/WebKit browsers** — `playwright install firefox webkit` for cross-browser section
6. **Stripe test cards** — already configured in Stripe test mode; use `4242 4242 4242 4242` (success), `4000 0000 0000 0002` (decline)

---

## Running Tests

```bash
./run_tests.sh
```

Seeds test data, runs the full suite, invokes a Claude analysis agent, and writes `reports/analysis_YYYY-MM-DD.md`. The HTML report is at `reports/report.html`.

Run a single section manually:
```bash
.venv/bin/pytest tests/test_01_environment.py -v
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

Before running pytest, always seed test data. The staging site runs under the `cscbooking` user with its own SQLite — seed that database, not the geoskimoto dev copy:

```bash
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data
```

This is idempotent. It ensures Alice has bookings, a $8,000 wallet, and an unread notification — prerequisites for sections 10, 11, 16, and 17.

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

**Known real bugs (always classify as `real_bug`, never `test_bug`):**
- `test_17_4_add_funds_entry_point` — wallet page has no Add Funds UI link
- `test_19_2_member_cannot_access_admin[/billing/admin-tool/]` — returns 500 instead of 403
- `test_21_responsive_dashboard[phone-viewport0]` — dashboard overflow at 375px

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
