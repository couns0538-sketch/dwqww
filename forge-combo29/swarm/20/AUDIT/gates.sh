#!/usr/bin/env bash
# gates.sh — seat 20: run every mechanical check I have, in one command, before pushing.
#
# Four checks, each with an exit-code contract, each written because it caught a real defect in my own work:
#   findings_lint.py    — duplicate ids / stale status / malformed rows      (caught 3 defects)
#   transcript_audit.py — engine transcript with a bestmove and no search    (caught seat 19's 222 files)
#   exe_identity_audit.py — post-rule job without an executable identity     (caught job74/75/79)
#   machine_clean.sh    — a leaked engine process or heavy load              (caught my own 3,400 s orphan)
#
# usage: gates.sh          exit 0 = all clear, non-zero = at least one failed (named at the end)
set -u
D="$(cd "$(dirname "$0")" && pwd)"
fail=""

run() { # label, then command
  local label="$1"; shift
  if "$@" > /tmp/gate.$$ 2>&1; then
    printf '  %-22s PASS\n' "$label"
  else
    printf '  %-22s FAIL\n' "$label"
    sed 's/^/      /' /tmp/gate.$$ | head -6
    fail="$fail $label"
  fi
}

echo "== seat 20 gates"
run findings_lint      python3 "$D/findings_lint.py"
run transcript_audit   python3 "$D/transcript_audit.py"
run exe_identity       python3 "$D/exe_identity_audit.py"
run machine_clean      bash "$D/machine_clean.sh"
rm -f /tmp/gate.$$

echo
if [ -z "$fail" ]; then
  echo "ALL GATES PASS — safe to push."
  exit 0
fi
echo "FAILED:$fail"
exit 1
