#!/bin/sh
# run_all_checks.sh : every script this seat cites as evidence, run TWICE - once in its own
# directory and once from an UNRELATED working directory. A checker whose verdict depends on
# where you stand is not a check (23-F227). Exits nonzero if any script fails, or if any
# script's two runs disagree (a script that only passes in its own folder is a defect).
SEAT=$(cd "$(dirname "$0")" && pwd)
FOREIGN=/tmp
fail=0
scripts="audit_findings.py doc_check.py rule_check.py
job68/final_recheck.py job69/frontpage_check.py
job70/verb_check.py job70/mech_check.py job70/sign_check.py
job11/tie_test.py"
printf "%-34s %-10s %-10s %s\n" "script" "own-dir" "foreign" "agree?"
for s in $scripts; do
  d=$(dirname "$SEAT/$s"); b=$(basename "$s")
  ( cd "$d" && timeout 600 python3 "$b" >/dev/null 2>&1 ); a=$?
  ( cd "$FOREIGN" && timeout 600 python3 "$SEAT/$s" >/dev/null 2>&1 ); c=$?
  agree="YES"
  if [ "$a" -ne "$c" ]; then agree="**NO - verdict depends on cwd**"; fail=1; fi
  if [ "$a" -ne 0 ] || [ "$c" -ne 0 ]; then fail=1; fi
  printf "%-34s %-10s %-10s %s\n" "$s" "$a" "$c" "$agree"
done
echo
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS - all scripts agree from both directories"; exit 0; fi
echo "VERDICT: FAIL"; exit 1
