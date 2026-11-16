#!/usr/bin/env bash
# long9_runs.sh -- R3 identities + R4's nine settings, on O and G, tunable build (and base for R3b).
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long9
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
TUN=/tmp/l9_tree/build/forge
BASE=/tmp/glmflash5_base/build/forge
O=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/first200.fens
G=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd
mkdir -p "$J/runs"
run() { # $1 exe, $2 tag, $3 setfile, $4 suffix
  local exe="$1" tag="$2" setf="$3" suffix="$4"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$L1/rows.py" --exe "$exe" --set "$setf" --out "$J/runs/$tag.rows" --depth 12 \
    --opts "$opts" --meta "$J/runs/$tag.rows.meta" > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
DS="LmrDeeperShallower=true"
jobs_n=0
for setname in O G; do
  [ "$setname" = O ] && setf="$O" || setf="$G"
  run "$TUN" "r3_def_$setname" "$setf" "" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$BASE" "r3b_base_$setname" "$setf" "$DS" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r3b_tun_$setname" "$setf" "$DS" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_k3_$setname" "$setf" "$DS;LmrDeeperBase=100000;LmrShallowerBase=-100000" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_k4a_$setname" "$setf" "$DS;LmrDeeperBase=20" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_k4b_$setname" "$setf" "$DS;LmrDeeperDepthMul=4" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_k4c_$setname" "$setf" "$DS;LmrShallowerBase=50" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_k4d_$setname" "$setf" "$DS;LmrShallowerDepthMul=3" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_deep_$setname" "$setf" "$DS;LmrShallowerBase=-100000" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_flat_$setname" "$setf" "$DS;LmrShallowerBase=8;LmrShallowerDepthMul=0" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_half_$setname" "$setf" "$DS;LmrDeeperBase=20;LmrDeeperDepthMul=1" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run "$TUN" "r4_dbl_$setname" "$setf" "$DS;LmrDeeperBase=80;LmrDeeperDepthMul=4" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
done
wait
echo "LONG9 RUNS DONE $(date -u)"
