#!/usr/bin/env bash
# job4_runs.sh -- Step 0's eight plain rows (B_FINE) and the D0..D3 counted runs (B_FINE_CTR).
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_job4
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
FINE=/tmp/j4_tree/build/forge
CTR=/tmp/j4_ctr/build/forge
O=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/first200.fens
G=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd
mkdir -p "$J/runs"
IDENT="LmrFine=1;LmrFineHistory=0;LmrRoundF=0"
T1="LmrFine=1;LmrFineHistory=1"
T2="LmrFine=1;LmrFineHistory=1;LmrRoundF=0"
jobs_n=0
run_fine() { # $1 tag, $2 setfile, $3 suffix
  local tag="$1" setf="$2" suffix="$3"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$L1/rows.py" --exe "$FINE" --set "$setf" --out "$J/runs/$tag.rows" --depth 12 \
    --opts "$opts" --meta "$J/runs/$tag.rows.meta" > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
run_ctr() { # $1 tag, $2 setfile, $3 suffix
  local tag="$1" setf="$2" suffix="$3"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$J/../tests_deepseek6_job3b/counterrun.py" --exe "$CTR" --set "$setf" --out "$J/runs/$tag.rows" \
    --cfp "$J/runs/$tag.lmrctr" --prefix lmrctr --depth 12 --opts "$opts" --meta "$J/runs/$tag.rows.meta" \
    > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
for setname in O G; do
  [ "$setname" = O ] && setf="$O" || setf="$G"
  for spec in "D0:" "D1:$IDENT" "D2:$T1" "D3:$T2"; do
    t="${spec%%:*}"; sfx="${spec#*:}"
    run_fine "fine_${setname}_${t}" "$setf" "$sfx" &
    jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
    run_ctr "${t}_${setname}" "$setf" "$sfx" &
    jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  done
done
wait
echo "JOB4 RUNS DONE $(date -u)"
