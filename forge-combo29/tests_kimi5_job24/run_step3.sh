#!/bin/bash
# kimi5 job 24 Step 3 driver: counting runs at depth 12 with the counting build.
# base on O+G, nc on O (known answer: tries with cut_node false = 0), t5 on O+G
# (refused-cutoff classification). The runner refuses to overwrite existing output.
set -u
JOB=/agent/repos/dwqww/forge-combo29/tests_kimi5_job24
EXE=/tmp/j24/build_cnt/forge
ROWS=$JOB/rows_count
mkdir -p "$ROWS"

run_one() {
  tag="$1"; set="$2"
  epd="$JOB/O.epd"; [ "$set" = G ] && epd="$JOB/G.epd"
  python3 "$JOB/runner_j18.py" "$EXE" "$epd" 12 "$ROWS" "cnt${tag}_${set}_d12" 100000 1 "$JOB/${tag}.opt" > "$ROWS/cnt${tag}_${set}_d12.stdout" 2>&1
}
export -f run_one
export JOB EXE ROWS

printf '%s\n' "base O" "base G" "nc O" "t5 O" "t5 G" | xargs -d '\n' -n 1 -P 4 bash -c 'run_one $1 $2' _
echo "== driver done $(date -u) =="
ls "$ROWS"/*_d12.json 2>/dev/null | wc -l
