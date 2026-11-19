#!/bin/bash
# kimi5 job 29 wave 2: counter runs on the counting build (rows_cnt/) and
# stretch tests on the plain build (rows/). Same runner, depth 12, O and G.
set -u
J=/agent/repos/dwqww/forge-combo29/tests_kimi5_job29
PLAIN=/tmp/b29/forge-combo29/build/forge
CNT=/tmp/b29cnt/build/forge
run_one() {
  exe="$1"; rows="$2"; tag="$3"; set="$4"
  epd="$J/O.epd"; [ "$set" = G ] && epd="$J/G.epd"
  python3 "$J/runner_j18.py" "$exe" "$epd" 12 "$rows" "${tag}_${set}_d12" 100000 1 "$J/opts/${tag}.opt" > "$rows/${tag}_${set}_d12.stdout" 2>&1
}
export -f run_one
export J
for tag in base hpd0 hpm20000 hpboth0 nmb6 nmdd1 dj8 hpm0; do for set in O G; do echo "$CNT $J/rows_cnt $tag $set"; done; done > /tmp/b29_wave2.txt
for tag in ced19 ced20 ced30 hbm9657 hbm9658 hbm10000; do for set in O G; do echo "$PLAIN $J/rows $tag $set"; done; done >> /tmp/b29_wave2.txt
mkdir -p "$J/rows_cnt"
cat /tmp/b29_wave2.txt | xargs -d '\n' -n 1 -P 4 bash -c 'run_one $1 $2 $3 $4' _
echo "== wave2 done $(date -u) =="
ls "$J/rows_cnt"/*_d12.json 2>/dev/null | wc -l
