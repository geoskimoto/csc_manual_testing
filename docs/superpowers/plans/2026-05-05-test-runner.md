# CSC Test Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the multi-phase loop system with a single `./run_tests.sh` command that seeds data, runs pytest, invokes a Claude analysis agent, and writes a dated markdown report.

**Architecture:** Two new files — `tester_prompt.md` (standing instructions for the analysis agent, tunable without touching the script) and `run_tests.sh` (bash entry point that orchestrates seed → pytest → claude → report). The agent receives the pytest JSON output inline in the prompt and writes its analysis to stdout, which the script redirects to `reports/analysis_YYYY-MM-DD.md`.

**Tech Stack:** bash, pytest (existing), Claude Code CLI (`claude --print`), pytest-json-report (existing)

---

### Task 1: Create `tester_prompt.md`

**Files:**
- Create: `tester_prompt.md` (project root)

- [ ] **Step 1: Create the prompt file**

Create `/home/geoskimoto/projects/csc_manual_testing/tester_prompt.md` with this exact content:

```markdown
You are a QA analyst for the Cascade Ski Club (CSC) booking system — a Django app at https://csc-booking-test.3rdplaces.io/ handling lodge bookings, wallet payments, Stripe payments, and membership subscriptions for a members-only ski club.

Your job: read the pytest JSON report provided at the end of this prompt and produce a structured markdown analysis report. You are acting as a manual tester reviewing automated test results. You have NO access to application source code — classify based on test output and error messages only.

**Do NOT modify test files or application code. Classify only.**

---

## Classification Rules

| Class | Meaning |
|---|---|
| `real_bug` | Site behavior is wrong — the test is correct. The app needs fixing. Include likely Django files to investigate. |
| `test_bug` | Test assertion is wrong — site behavior is acceptable. The test needs updating, not the app. Include the suggested fix. |
| `missing_data` | Test requires DB state that `seed_test_data` didn't create. This is a gap in test infrastructure, not an app bug. |

**Classification guidance:**
- A skip is `missing_data` if the test's skip guard checks for DB state (e.g., "no bookings found", "no notifications found")
- A skip is `test_bug` if the skip guard condition is itself wrong
- When a failure message mentions a selector mismatch (e.g., "strict mode violation", "locator resolved to N elements"), check whether the site behavior is correct before calling it a bug — it may be a `test_bug` caused by a stale selector
- `likely_files` for `real_bug` entries should name Django app files (views, templates, models) — never test files

## Known Baselines

Apply these classifications consistently — do not re-litigate them:

- `test_8_1_stripe_success_payment`, `test_8_2_stripe_declined_card` → **test_bug**: Stripe Link injects a second iframe into `#card-number-element`. The site behavior is correct. The test locator `#card-number-element iframe` is too broad (strict mode violation). Fix: use `page.frame_locator('#card-number-element iframe').first` or filter by title attribute.
- Tests in sections 10 and 11 that skip with "No bookings found" → **missing_data**: booking detail link selector `a[href*='/dashboard/booking_detail/']` does not match the app's actual URL pattern. Needs DOM inspection.
- `test_16_4_individual_notification_mark_read` skip → **missing_data**: notifications page only exposes bulk "Mark All Read", no per-notification mark-read link in the current UI.

## Sections Not Yet Written

The following HUMAN_TESTER_GUIDE.md sections have no test file and should be listed in the report:
- Section 2 (Registration / Onboarding)
- Section 5 (Family Booking)
- Section 6 (Guest Booking)
- Section 12 (Admin Booking) — needs admin credentials
- Section 13 (Admin Manage) — needs admin credentials
- Section 15 (Invoicing) — needs financial admin credentials
- Section 22 (Cross-Browser) — requires Firefox/WebKit installs
- Section 23 (Race Conditions) — partial coverage only

---

## Output Format

Write the report in this exact structure:

```
# CSC Test Analysis — {DATE}

## Summary

| Passed | Failed | Skipped | Total |
|--------|--------|---------|-------|
| X      | X      | X       | X     |

## Real Bugs _(app needs fixing)_

### `test_id`
- **Description:** What the test does, what it found, why this is an app bug
- **Likely files:** list of Django app files to investigate

_(or: "None — zero real_bug failures this run.")_

## Test Bugs _(test needs updating, not the app)_

### `test_id`
- **Description:** What the test asserts and why the assertion is wrong
- **Suggested fix:** concrete selector or assertion change

_(or: "None.")_

## Missing Data / Skips

### Group name
- **Affected tests:** list of test IDs
- **Description:** what DB state is missing or what selector/URL mismatch causes the skip
- **Gap:** what this means for test coverage

_(or: "None — all tests either passed, failed, or were classified above.")_

## Sections Not Yet Written

- Section N — Topic (reason if known)

## Recommendations

Prioritized list — what should the fix agent tackle first? Include: fix real bugs (most urgent), investigate missing data gaps, update test bugs.
```

Replace `{DATE}` with the date provided below.
Write the completed report to the output file path provided below.
```

- [ ] **Step 2: Verify the file exists and is readable**

```bash
wc -l /home/geoskimoto/projects/csc_manual_testing/tester_prompt.md
```

Expected: prints a line count (should be ~80+ lines). Any output means the file was created.

- [ ] **Step 3: Commit**

```bash
cd /home/geoskimoto/projects/csc_manual_testing
git add tester_prompt.md
git commit -m "feat: add tester_prompt.md for analysis agent standing instructions"
```

---

### Task 2: Create `run_tests.sh`

**Files:**
- Create: `run_tests.sh` (project root)

- [ ] **Step 1: Create the script**

Create `/home/geoskimoto/projects/csc_manual_testing/run_tests.sh` with this exact content:

```bash
#!/bin/bash
# CSC test runner — seeds data, runs pytest, invokes Claude analysis agent
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DATE=$(date +%F)
DATETIME=$(date +"%F %H:%M")
REPORT_JSON="reports/report.json"
REPORT_HTML="reports/report.html"
ANALYSIS_FILE="reports/analysis_${DATE}.md"

echo "=== CSC Test Runner — ${DATETIME} ==="
echo ""

# ── Step 1: Seed test data ──────────────────────────────────────────────────
echo ">>> Seeding test data..."
sudo -u cscbooking \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/venv/bin/python \
  /home/cscbooking/htdocs/csc-booking-test.3rdplaces.io/manage.py seed_test_data \
  && echo "    Seed complete." \
  || { echo "ERROR: seed_test_data failed. Aborting."; exit 1; }
echo ""

# ── Step 2: Run tests ───────────────────────────────────────────────────────
echo ">>> Running tests (output below)..."
echo "──────────────────────────────────────────────────────────────────────"
mkdir -p reports

.venv/bin/pytest -v --tb=short \
  --json-report --json-report-file="$REPORT_JSON" \
  --html="$REPORT_HTML"
PYTEST_EXIT=$?

echo "──────────────────────────────────────────────────────────────────────"
echo ""

# Exit code 5 = no tests collected — that's a real problem
if [ "$PYTEST_EXIT" -eq 5 ]; then
  echo "ERROR: pytest collected no tests. Check your test files and conftest.py."
  exit 1
fi

# Exit codes 0 (all pass) and 1 (some fail) are both fine — failures get classified
# Codes 2-4 are pytest infrastructure errors
if [ "$PYTEST_EXIT" -gt 1 ]; then
  echo "ERROR: pytest exited with code $PYTEST_EXIT (infrastructure error, not test failure)."
  exit 1
fi

if [ ! -f "$REPORT_JSON" ]; then
  echo "ERROR: $REPORT_JSON was not created. Cannot run analysis."
  exit 1
fi

# ── Step 3: Invoke Claude analysis agent ─────────────────────────────────────
echo ">>> Running analysis agent..."

JSON_CONTENT=$(cat "$REPORT_JSON")
PROMPT_TEMPLATE=$(cat tester_prompt.md)

FULL_PROMPT="${PROMPT_TEMPLATE}

---
Today's date: ${DATE}
Output file: ${ANALYSIS_FILE}

<pytest_results>
${JSON_CONTENT}
</pytest_results>"

claude --print "$FULL_PROMPT" > "$ANALYSIS_FILE"
CLAUDE_EXIT=$?

if [ "$CLAUDE_EXIT" -ne 0 ] || [ ! -s "$ANALYSIS_FILE" ]; then
  echo "ERROR: Claude analysis failed or produced an empty report (exit $CLAUDE_EXIT)."
  exit 1
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "=== Done ==="
echo "  Analysis: $ANALYSIS_FILE"
echo "  HTML:     $REPORT_HTML"
echo "  JSON:     $REPORT_JSON"
```

- [ ] **Step 2: Make the script executable**

```bash
chmod +x /home/geoskimoto/projects/csc_manual_testing/run_tests.sh
```

- [ ] **Step 3: Verify the script is syntactically valid**

```bash
bash -n /home/geoskimoto/projects/csc_manual_testing/run_tests.sh
```

Expected: no output (silent = valid syntax).

- [ ] **Step 4: Commit**

```bash
cd /home/geoskimoto/projects/csc_manual_testing
git add run_tests.sh
git commit -m "feat: add run_tests.sh — single-command test runner with Claude analysis"
```

---

### Task 3: Smoke Test the Runner

**Goal:** Verify the script runs end-to-end and produces a non-empty analysis report.

- [ ] **Step 1: Run the script**

```bash
cd /home/geoskimoto/projects/csc_manual_testing
./run_tests.sh
```

Expected terminal output (approximate):
```
=== CSC Test Runner — 2026-05-05 HH:MM ===

>>> Seeding test data...
    Seed complete.

>>> Running tests (output below)...
──────────────────────────────────────────
... pytest output ...
──────────────────────────────────────────

>>> Running analysis agent...

=== Done ===
  Analysis: reports/analysis_2026-05-05.md
  HTML:     reports/report.html
  JSON:     reports/report.json
```

- [ ] **Step 2: Verify the report file was created and is non-empty**

```bash
wc -l /home/geoskimoto/projects/csc_manual_testing/reports/analysis_$(date +%F).md
```

Expected: 30+ lines.

- [ ] **Step 3: Spot-check report structure**

```bash
grep -E "^## " /home/geoskimoto/projects/csc_manual_testing/reports/analysis_$(date +%F).md
```

Expected output should include all major sections:
```
## Summary
## Real Bugs
## Test Bugs
## Missing Data / Skips
## Sections Not Yet Written
## Recommendations
```

- [ ] **Step 4: Update CLAUDE.md to document the new runner and retire loop system references**

In `/home/geoskimoto/projects/csc_manual_testing/CLAUDE.md`, replace the "Planner Agent — Automated Loop Behavior" section header and its content with:

```markdown
## Running Tests

```bash
./run_tests.sh
```

Seeds test data, runs the full suite, invokes a Claude analysis agent, and writes `reports/analysis_YYYY-MM-DD.md`. The HTML report is at `reports/report.html`.

The analysis agent instructions live in `tester_prompt.md` — edit that file to update classification rules or report format without touching the script.

Run a single section manually:
```bash
.venv/bin/pytest tests/test_01_environment.py -v
```
```

- [ ] **Step 5: Final commit**

```bash
cd /home/geoskimoto/projects/csc_manual_testing
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — document run_tests.sh, retire loop system docs"
```
