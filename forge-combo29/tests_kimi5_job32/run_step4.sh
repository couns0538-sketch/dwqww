#!/bin/bash
# kimi5 job 32 Step 4: the flat-map checks at go nodes 20000, O and G, a fresh process per
# setting, the class build. T = top of the tuned range, B = the O bound (from measured DMAX),
# Bm = B-1. The base rows are the KA-A cls_*_n20000 runs.
set -u
J=/agent/repos/dwqww/forge-combo29/tests_kimi5_job32
CLS=/tmp/j32/cls/build/forge
ROWS="$J/rows4"
mkdir -p "$ROWS"
run() { # tag set
  local epd="$J/O.epd"; [ "$2" = G ] && epd="$J/G.epd"
  python3 "$J/runner_j32.py" "$CLS" "$epd" "nodes 20000" "$ROWS" "$1_$2_n20000" 100000 1 "$J/opts/$1.opt" > "$ROWS/$1_$2_n20000.stdout" 2>&1
}
export J CLS ROWS
export -f run
TAGS="rfpdT rfpdB rfpdBm futdT futdB futdBm singdT singdB singdBm iirdT iirdB iirdBm pbdT pbdB pbdBm cedT cedB cedBm hbmT hbmB hbmBm"
for tag in $TAGS; do for set in O G; do echo "$tag $set"; done; done | xargs -d '\n' -n 1 -P 4 bash -c 'run $1 $2' _
echo "== step4 runs done $(date -u) =="
ls "$ROWS"/*.json 2>/dev/null | wc -l
