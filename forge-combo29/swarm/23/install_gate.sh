#!/usr/bin/env bash
# pre-commit hook for this seat: refuse a commit whose documents fail the three structural checks.
#
# WHY THIS EXISTS: three times in one session a literal pipe inside a markdown table cell split a row (23-F83, F122,
# F147), and each time the finding-table audit caught it — but only because I happened to run the audit afterwards. A
# check that depends on being remembered is not a gate. This hook makes it unskippable for the files it covers.
#
# Installed as .git/hooks/pre-commit in the repo root; it only acts on commits that touch forge-combo29/swarm/23.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 0
SEAT="forge-combo29/swarm/23"

# only run when this commit touches the seat
if ! git diff --cached --name-only | grep -q "^$SEAT/"; then
  exit 0
fi
if [ ! -d "$SEAT" ]; then
  exit 0
fi

fail=0
run() {
  local name="$1" script="$2"
  if [ ! -f "$SEAT/$script" ]; then
    echo "pre-commit: $name SKIPPED (no $SEAT/$script)"
    return
  fi
  if ( cd "$SEAT" && python3 "$script" >/tmp/precommit_$name.log 2>&1 ); then
    echo "pre-commit: $name PASS"
  else
    echo "pre-commit: $name FAIL — see /tmp/precommit_$name.log"
    tail -6 /tmp/precommit_$name.log | sed 's/^/    /'
    fail=1
  fi
}

run findings audit_findings.py
run docs     doc_check.py
run rules    rule_check.py

if [ "$fail" -ne 0 ]; then
  echo
  echo "pre-commit: BLOCKED. Fix the failure above, or commit with --no-verify if it is genuinely unrelated"
  echo "            (and say why in the commit message if you do)."
  exit 1
fi
exit 0
