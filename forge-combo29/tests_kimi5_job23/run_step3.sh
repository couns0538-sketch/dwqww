#!/bin/bash
# kimi5 job 23 Step 3 driver: the counting build (observe-only LMRF lines) under base
# (PC20; LmrFine at its default 0), O and G, depth 12. The runner refuses to overwrite.
set -u
DEPTH=12
JOB=/agent/repos/dwqww/forge-combo29/tests_kimi5_job23
EXE=/tmp/j23/build-count/forge
ROWS=$JOB/rows_count
mkdir -p "$ROWS"

run_one() {
  set="$1"
  epd="$JOB/O.epd"; [ "$set" = G ] && epd="$JOB/G.epd"
  python3 "$JOB/runner_j18.py" "$EXE" "$epd" "$DEPTH" "$ROWS" "count_${set}_d${DEPTH}" 100000 1 "$JOB/base.opt" > "$ROWS/count_${set}_d${DEPTH}.stdout" 2>&1
}
export -f run_one
export JOB EXE ROWS DEPTH

printf 'O\nG\n' | xargs -d '\n' -n 1 -P 2 bash -c 'run_one $1' _
echo "== counting driver done $(date -u) =="
grep -c "^LMRF" "$ROWS"/count_*_d${DEPTH}_full.txt
