#!/usr/bin/env bash
# integrity_selftest.sh : prove compare_perft.py FAILS LOUDLY when a number is missing, empty or NaN.
# Seat 19's warning: a check must never print a confirmation when its parse found nothing.
# Each case builds a tiny fake data set in a scratch dir and runs the real comparison script.
set -u
SCRIPT=/agent/repos/dwqww/forge-combo29/swarm/23/job1/compare_perft.py
T=$(mktemp -d)
cd "$T" || exit 1

row_ok_eng='{"i":0,"fen":"8/8/8/8/8/8/8/K6k w - - 0 1","nodes":{"1":3,"2":9,"3":27,"4":81},"divide":{}}'
row_ok_ref='{"i":0,"fen":"8/8/8/8/8/8/8/K6k w - - 0 1","invalid":false,"nodes":{"1":3,"2":9,"3":27,"4":81}}'

case_run() {
  name="$1"; eng="$2"; ref="$3"
  rm -f ./*.jsonl
  printf '%s\n' "$eng" > engine_R.jsonl
  printf '%s\n' "$ref" > pych_R_0.jsonl
  out=$(python3 "$SCRIPT" 2>&1); code=$?
  verdict=$(printf '%s' "$out" | grep -c "HARD FAILURE")
  printf 'case %-28s exit=%d hard_failure_lines=%d\n' "$name" "$code" "$verdict"
  printf '%s\n' "$out" | sed 's/^/    /' | head -4
}

echo "== cases that MUST fail (exit 2, HARD FAILURE)"
case_run "empty engine file"  ''            "$row_ok_ref"
case_run "empty reference file" "$row_ok_eng" ''
case_run "missing depth 3 row" '{"i":0,"fen":"x","nodes":{"1":3,"2":9,"4":81}}' "$row_ok_ref"
case_run "nodes is a string" '{"i":0,"fen":"x","nodes":{"1":"3","2":9,"3":27,"4":81}}' "$row_ok_ref"
case_run "nodes is null"     '{"i":0,"fen":"x","nodes":{"1":null,"2":9,"3":27,"4":81}}' "$row_ok_ref"
case_run "row without nodes" '{"i":0,"fen":"x"}' "$row_ok_ref"
case_run "reference without invalid flag" "$row_ok_eng" '{"i":0,"fen":"x","nodes":{"1":3,"2":9,"3":27,"4":81}}'

echo
echo "== case that MUST pass (exit 0, real numbers, 'positions actually compared: 1')"
case_run "clean single row" "$row_ok_eng" "$row_ok_ref"

rm -rf "$T"
