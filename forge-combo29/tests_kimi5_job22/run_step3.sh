#!/bin/bash
# kimi5 job 22 Step 3 driver: counting-build rows for base and sf on O and G, depth 12.
# usage: run_step3.sh
set -u
JOB=/agent/repos/dwqww/forge-combo29/tests_kimi5_job22
EXE=/tmp/j22/build-cnt/forge
ROWS=$JOB/rows
mkdir -p "$ROWS"

run_one() {
  tag="$1"; set="$2"
  epd="$JOB/O.epd"; [ "$set" = G ] && epd="$JOB/G.epd"
  python3 "$JOB/runner_j18.py" "$EXE" "$epd" 12 "$ROWS" "cnt${tag}_${set}_d12" 100000 1 "$JOB/${tag}.opt" > "$ROWS/cnt${tag}_${set}_d12.stdout" 2>&1
}
export -f run_one
export JOB EXE ROWS

printf '%s\n' "base O" "base G" "sf O" "sf G" | xargs -d '\n' -n 1 -P 4 bash -c 'run_one $1' _
echo "== step3 driver done $(date -u) =="
ls "$ROWS"/cnt*_d12.json 2>/dev/null | wc -l
