#!/bin/bash
# kimi5 job 29 row driver: fixed-depth-12 rows per setting on O and G (PC20 base).
# One runner process per (setting, set); at most 4 at a time; runner refuses overwrite.
set -u
EXE="$1"; ROWS="$2"; DEPTH=12
JOB=/agent/repos/dwqww/forge-combo29/tests_kimi5_job29
TAGS="base identity hpd0 hpm20000 hpboth0 nmb6 nmdd1 dj8 hpd10 cfb1000 hpm0 nmb4"
mkdir -p "$ROWS"
run_one() {
  tag="$1"; set="$2"
  epd="$JOB/O.epd"; [ "$set" = G ] && epd="$JOB/G.epd"
  python3 "$JOB/runner_j18.py" "$EXE" "$epd" "$DEPTH" "$ROWS" "${tag}_${set}_d${DEPTH}" 100000 1 "$JOB/opts/${tag}.opt" > "$ROWS/${tag}_${set}_d${DEPTH}.stdout" 2>&1
}
export -f run_one
export JOB EXE ROWS DEPTH
for tag in $TAGS; do for set in O G; do echo "$tag $set"; done; done | xargs -d '\n' -n 1 -P 4 bash -c 'run_one $1' _
echo "== driver done $(date -u) =="
ls "$ROWS"/*_d${DEPTH}.json 2>/dev/null | wc -l
