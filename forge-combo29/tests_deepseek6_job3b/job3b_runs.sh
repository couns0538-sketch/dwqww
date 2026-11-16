#!/usr/bin/env bash
# job3b_runs.sh -- the 14 counted runs (C0..C6 on O and G) with the counter build.
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_job3b
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
EXE=/tmp/j3b_edit/build/forge
O=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/first200.fens
G=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd
mkdir -p "$J/runs"
run() { # $1 tag, $2 setfile, $3 opts-suffix (may be empty)
  local tag="$1" setf="$2" suffix="$3"
  if [ -s "$J/runs/$tag.rows" ]; then echo "skip $tag"; return 0; fi
  local opts="$S14"
  [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$J/counterrun.py" --exe "$EXE" --set "$setf" --out "$J/runs/$tag.rows" \
    --cfp "$J/runs/$tag.cfp" --depth 12 --opts "$opts" --meta "$J/runs/$tag.rows.meta" \
    > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
for setname in O G; do
  [ "$setname" = O ] && setf="$O" || setf="$G"
  run "C0_$setname" "$setf" ""
  run "C1_$setname" "$setf" "CaptureFutilityBase=230"
  run "C2_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityDepth=5"
  run "C3_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityDepth=7"
  run "C4_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityMultiplier=100"
  run "C5_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityMultiplier=100;CaptureFutilityDepth=5"
  run "C6_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityMultiplier=100;CaptureFutilityDepth=9"
done
echo "JOB3B RUNS DONE $(date -u)"
