#!/usr/bin/env bash
# R5B final checks from the branch head: rebuild OFF and N2 for both recipes, compare them with the exes the report
# and the proposal name (only the PE timestamp may differ: cmp -l must print 4 differing bytes), run the lock
# identity on every rebuilt exe and on the two M1-fix OFF exes (the "after M1" rows of rule 7), and print the
# kernel line and the parity-test label of the N2 builds.
# usage: bash opus_r5/r5b/tools/final_checks.sh <worktree> <tag>      (tag = short head commit)
set -uo pipefail
WT=$1; TAG=$2
E=/f/opus_scratch/r5/r5b/exe
L="$WT/opus_r5/r5b/logs"
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
N2="-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1"
declare -A REF=([off_z5]=forge_r5b_off_z5_m1fix.exe [off_v3]=forge_r5b_off_v3_m1fix.exe
                [n2_z5]=forge_r5b_n2_z5_b2983d07.exe [n2_v3]=forge_r5b_n2_v3_b2983d07.exe)
for n in off_z5 off_v3 n2_z5 n2_v3; do
  rec=$([ "${n#*_}" = z5 ] && echo znver5 || echo v3)
  fl=$([ "${n%_*}" = n2 ] && echo "$N2" || echo "")
  # shellcheck disable=SC2086
  RECIPE=$rec bash "$WT/opus_r5/r5b/tools/build_r5b.sh" "$WT" "$E/forge_r5b_${n}_final_$TAG.exe" $fl > "$L/build_${n}_final_$TAG.log" 2>&1 \
    || { echo "build $n failed"; exit 1; }
  echo "$n final: $(grep -c -i warning "$L/build_${n}_final_$TAG.log") warnings, $(grep FMA "$L/build_${n}_final_$TAG.log"), differs from ${REF[$n]} in $(cmp -l "$E/forge_r5b_${n}_final_$TAG.exe" "$E/${REF[$n]}" | wc -l) bytes"
done
ids="off_z5_final_$TAG off_v3_final_$TAG n2_z5_final_$TAG n2_v3_final_$TAG off_z5_m1fix off_v3_m1fix"
i=0
for n in $ids; do
  (nice -n 10 "$PY" -I -B "$LA/2_build/uci_check.py" "$E/forge_r5b_$n.exe" --full 2>&1 | tr -d '\r' > "$L/identity_$n.log") &
  i=$((i + 1)); [ $((i % 3)) -eq 0 ] && wait
done
wait
for n in $ids; do echo "identity $n: $(tail -1 "$L/identity_$n.log")"; done
for n in n2_z5 n2_v3; do
  echo "$n final uci line: $( (printf 'uci\n'; sleep 1; printf 'quit\n') | "$E/forge_r5b_${n}_final_$TAG.exe" | grep 'nnue kernel' | tr -d '\r')"
done
