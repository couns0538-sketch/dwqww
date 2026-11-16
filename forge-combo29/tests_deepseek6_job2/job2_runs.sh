#!/usr/bin/env bash
# job2_runs.sh -- Part A (4 settings x 4 values x 2 sets) and Part B (5 configs x 2 sets).
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_job2
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
EXE=/tmp/glmflash5_base/build/forge
O=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/first200.fens
G=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd
mkdir -p "$J/runs"
run() { # $1 tag, $2 setfile, $3 opts-suffix
  local tag="$1" setf="$2" suffix="$3"
  if [ -s "$J/runs/$tag.rows" ]; then echo "skip $tag"; return 0; fi
  python3 "$L1/rows.py" --exe "$EXE" --set "$setf" --out "$J/runs/$tag.rows" --depth 12 \
    --opts "${S14};${suffix}" --meta "$J/runs/$tag.rows.meta" > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
# Part A: setting|v(2c-)|v(2c+)|v(4c-)|v(4c+)
cat > "$J/partA_table.txt" <<'EOF'
NullMoveEvalDivisor 160 240 120 280
RfpDepth 6 10 4 12
FutilityDepth 5 9 3 11
SeeNoisyMultiplier 126 174 102 198
EOF
jobs_n=0
while read -r n v1 v2 v3 v4; do
  i=0
  for spec in "a2m:$v1" "a2p:$v2" "a4m:$v3" "a4p:$v4"; do
    t="${spec%%:*}"; v="${spec#*:}"
    for setname in O G; do
      [ "$setname" = O ] && setf="$O" || setf="$G"
      run "${n}_${setname}_${t}" "$setf" "${n}=${v}" &
      jobs_n=$((jobs_n+1))
      if [ $((jobs_n % 3)) -eq 0 ]; then wait; fi
    done
  done
done < "$J/partA_table.txt"
wait
# Part B
for setname in O G; do
  [ "$setname" = O ] && setf="$O" || setf="$G"
  run "B0_$setname" "$setf" "CaptureFutilityBase=230"
  run "B1_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityMultiplier=225"
  run "B2_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityMultiplier=275"
  run "B3_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityDepth=5"
  run "B4_$setname" "$setf" "CaptureFutilityBase=230;CaptureFutilityDepth=7"
done
echo "JOB2 RUNS DONE $(date -u)"
