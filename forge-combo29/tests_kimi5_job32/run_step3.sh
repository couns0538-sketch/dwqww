#!/bin/bash
# kimi5 job 32 Step 3: the conditions. go depth 12 on O and G, a fresh process per setting,
# the class build. The base runs are the KA-A cls_*_d12 runs (same build/opts/limit).
set -u
J=/agent/repos/dwqww/forge-combo29/tests_kimi5_job32
CLS=/tmp/j32/cls/build/forge
ROWS="$J/rows3"
mkdir -p "$ROWS"
run() { # tag set
  local epd="$J/O.epd"; [ "$2" = G ] && epd="$J/G.epd"
  python3 "$J/runner_j32.py" "$CLS" "$epd" "depth 12" "$ROWS" "$1_$2_d12" 100000 1 "$J/opts/$1.opt" > "$ROWS/$1_$2_d12.stdout" 2>&1
}
export J CLS ROWS
export -f run
TAGS="lqb99 lqb100 lqd161 lqd160 lmp19 lmp20 lqb300 lqb100_hpd0 lqb100_hpm20000 lqb100_hpboth0 lqd160_hpd0 lqd160_hpm20000 lqd160_hpboth0 lmp20_hpd0 lmp20_hpm20000 lmp20_hpboth0"
for tag in $TAGS; do for set in O G; do echo "$tag $set"; done; done | xargs -d '\n' -n 1 -P 4 bash -c 'run $1 $2' _
echo "== step3 runs done $(date -u) =="
ls "$ROWS"/*_d12.json 2>/dev/null | wc -l
