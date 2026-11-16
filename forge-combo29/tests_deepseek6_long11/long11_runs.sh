#!/usr/bin/env bash
# long11_runs.sh -- R3 identities (both builds, S14) + R4's four flag runs.
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long11
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
NOFLAG=/tmp/l11_noflag/build/forge
FLAG=/tmp/l11_flag/build/forge
O=$L1/first200.fens
G=$L1/set_G.epd
head -50 "$G" > /tmp/g50.fens
head -50 "$O" > /tmp/o50.fens
mkdir -p "$J/runs"
jobs_n=0
run_nf() { # $1 tag, $2 setfile, $3 suffix
  local tag="$1" setf="$2" suffix="$3"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$L1/rows.py" --exe "$NOFLAG" --set "$setf" --out "$J/runs/$tag.rows" --depth 12 \
    --opts "$opts" --meta "$J/runs/$tag.rows.meta" > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
run_fl() { # $1 tag, $2 setfile, $3 depth, $4 suffix
  local tag="$1" setf="$2" depth="$3" suffix="$4"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$J/chkrun.py" --exe "$FLAG" --set "$setf" --out "$J/runs/$tag.rows" \
    --chk "$J/runs/$tag.chk" --depth "$depth" --opts "$opts" --meta "$J/runs/$tag.rows.meta" \
    > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
# R3: S14 identities on both builds
for setname in O G; do
  [ "$setname" = O ] && setf="$O" || setf="$G"
  run_nf "r3_noflag_$setname" "$setf" "" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
  run_fl "r3_flag_$setname" "$setf" 12 "" &
  jobs_n=$((jobs_n+1)); [ $((jobs_n % 3)) -eq 0 ] && wait
done
wait
# R4: the four measured runs, flag build, no options
run_fl "r4_O_d12" "$O" 12 "" &
run_fl "r4_G_d12" "$G" 12 "" &
run_fl "r4_G50_d16" /tmp/g50.fens 16 "" &
run_fl "r4_O50_T4" /tmp/o50.fens 12 "Threads=4" &
wait
echo "LONG11 RUNS DONE $(date -u)"
