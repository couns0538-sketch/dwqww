#!/bin/bash
# kimi5 job 24 Step 1+2 driver: fixed-depth rows for the given settings on O and G.
# One runner process per (setting, set); at most 4 at a time; the runner refuses to
# overwrite any existing output. usage: run_step1.sh <depth> [tag ...]
set -u
DEPTH="$1"; shift || true
TAGS="$*"; [ -z "$TAGS" ] && TAGS="base nc t5 both"
JOB=/agent/repos/dwqww/forge-combo29/tests_kimi5_job24
EXE=/tmp/j24/build/forge
ROWS=$JOB/rows
mkdir -p "$ROWS"

gen_lines() {
  for tag in $TAGS; do
    for set in O G; do
      echo "$tag $set"
    done
  done
}

run_one() {
  tag="$1"; set="$2"
  epd="$JOB/O.epd"; [ "$set" = G ] && epd="$JOB/G.epd"
  python3 "$JOB/runner_j18.py" "$EXE" "$epd" "$DEPTH" "$ROWS" "${tag}_${set}_d${DEPTH}" 100000 1 "$JOB/${tag}.opt" > "$ROWS/${tag}_${set}_d${DEPTH}.stdout" 2>&1
}
export -f run_one
export JOB EXE ROWS DEPTH

gen_lines | xargs -d '\n' -n 1 -P 4 bash -c 'run_one $1' _
echo "== driver done $(date -u) =="
ls "$ROWS"/*_d${DEPTH}.json 2>/dev/null | wc -l
