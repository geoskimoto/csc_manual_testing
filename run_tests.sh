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
mkdir -p tests/screenshots
# Ensure screenshot files are writable by the current user (prior runs as root can leave root-owned files)
sudo chown -R "$(whoami)" tests/screenshots/ 2>/dev/null || true

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

<pytest_results>
${JSON_CONTENT}
</pytest_results>"

printf '%s' "$FULL_PROMPT" | claude --print > "$ANALYSIS_FILE"
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
