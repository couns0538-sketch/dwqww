#!/usr/bin/env bash
# long22_runs.sh -- the six real TSan runs (3 configs x Threads 2,4), first 50 of O, depth 12.
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long22
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
mkdir -p "$J/runs"
run() { # $1 exe, $2 tag, $3 threads, $4 opts-extra
  local exe="$1" tag="$2" thr="$3" extra="$4"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"
  [ -n "$extra" ] && opts="${S14};${extra}"
  env -u TSAN_OPTIONS python3 "$J/tsanrun.py" --exe "$exe" --set /tmp/o50.fens \
    --out "$J/runs/$tag.rows" --depth 12 --opts "Threads=$thr;${opts}" > "$J/runs/$tag.log" 2>&1
  echo "done $tag rc=$?"
}
run /tmp/l22_plain/build/forge "plain_t2" 2 ""
run /tmp/l22_plain/build/forge "plain_t4" 4 ""
run /tmp/l22_fine/build/forge  "fine_t2"  2 "LmrFine=1;LmrFineHistory=1;LmrRoundF=0"
run /tmp/l22_fine/build/forge  "fine_t4"  4 "LmrFine=1;LmrFineHistory=1;LmrRoundF=0"
run /tmp/l22_fhb/build/forge   "fhb7_t2"  2 "FailHighBlend=7"
run /tmp/l22_fhb/build/forge   "fhb7_t4"  4 "FailHighBlend=7"
echo "LONG22 RUNS DONE $(date -u)"
