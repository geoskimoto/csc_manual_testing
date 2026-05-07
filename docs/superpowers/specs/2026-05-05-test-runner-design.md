# CSC Test Runner — Design Spec
**Date:** 2026-05-05  
**Status:** Approved

---

## Problem

The existing loop system (state machine with cycle counting, handoff JSON, fix-agent prompt generation, multi-phase coordination) is too slow and inconsistent for practical use. The core value it provides — intelligent failure classification — is buried in infrastructure.

---

## Goal

A single bash command that:
1. Seeds test data
2. Runs the Playwright test suite
3. Invokes a Claude analysis agent to classify failures
4. Writes a markdown report ready to hand to a fix agent

No state machine. No cycle tracking. No automated fix pipeline. One shot, one report.

---

## Components

### 1. `run_tests.sh`

Entry point. Runs in sequence:

```
1. seed test data (sudo -u cscbooking manage.py seed_test_data)
2. pytest → reports/report.json + reports/report.html
3. claude --print [analysis agent] → reports/analysis_YYYY-MM-DD.md
4. print path to report
```

Lives at the project root. Executable (`chmod +x`).

Exits with a non-zero code if pytest fails to run (not if tests fail — failures are expected and classified).

### 2. `tester_prompt.md`

The analysis agent's standing instructions. Kept as a separate file so it can be tuned without touching the script.

The agent's job mirrors the loop planner's classification logic:

| Class | Meaning |
|---|---|
| `real_bug` | Site behavior is wrong — test is correct. Needs a fix in the app. |
| `test_bug` | Test assertion is wrong — site behavior is acceptable. Test needs updating. |
| `missing_data` | Test requires DB state that seed_test_data didn't create. Gap in test infrastructure. |

The agent reads `reports/report.json`, classifies every failure and skip with reasoning, and writes the markdown report. It does **not** modify test files or application code.

### 3. `reports/analysis_YYYY-MM-DD.md`

Output report. Structure:

```
# CSC Test Analysis — YYYY-MM-DD HH:MM

## Summary
| Passed | Failed | Skipped | Total |

## Real Bugs  (app needs fixing)
### test_id
- Classification: real_bug
- Description: what the test does, what it found, why this is an app bug
- Likely files: [list]

## Test Bugs  (test needs updating)
### test_id
- Classification: test_bug
- Description: what the test asserts, why the assertion is wrong, suggested fix

## Missing Data / Skips
### test group
- Description: what DB state is missing and why tests skip

## Sections Not Yet Written
- List of HUMAN_TESTER_GUIDE.md sections with no test file

## Recommendations
- Prioritized list of what to fix or investigate next
```

---

## Data Flow

```
run_tests.sh
  │
  ├─ sudo -u cscbooking python manage.py seed_test_data
  │    └─ ensures: Alice $8k wallet, active subscription, past/future bookings, unread notification
  │
  ├─ .venv/bin/pytest -v --tb=short
  │    --json-report --json-report-file=reports/report.json
  │    --html=reports/report.html
  │
  └─ claude --print -p "[tester_prompt.md content + injected date + JSON path]"
       │    stdout captured → reports/analysis_YYYY-MM-DD.md
       └─ reads: reports/report.json (path injected into prompt by the script)
       └─ writes: reports/analysis_YYYY-MM-DD.md (via stdout redirect)
```

---

## Classification Rules (for `tester_prompt.md`)

The agent follows the same rules as the loop planner. Key guidance:

- **Do NOT modify test files** — tests are a locked specification
- **Do NOT modify application code** — analysis only
- A test that skips is classified under `missing_data` if the skip is conditional on DB state; it's `test_bug` if the skip guard is itself wrong
- Failures with known root causes (Stripe Link iframe ambiguity, booking detail URL mismatch) should be classified consistently with prior analysis
- `likely_files` for real bugs should name Django app files, not test files

---

## What This Replaces

The following loop-system artifacts are **not** part of this design:

- `cycle/state.json` — no cycle state
- `cycle/handoff_{N}.json` — no structured handoff; the markdown report is the handoff
- `cycle/plan_{N}.md` — merged into the analysis report
- Fix agent prompt files — the human manages the fix agent manually
- `nightly_tasks/run_task.sh` — replaced by `run_tests.sh`

The `cycle/` directory and its existing files are left in place but are no longer written to.

---

## Out of Scope

- Multi-cycle tracking or stall detection
- Fix agent invocation
- Cross-browser testing (Firefox/WebKit) — requires separate playwright install
- Admin/financial account test sections (12, 13, 15) — no credentials yet
