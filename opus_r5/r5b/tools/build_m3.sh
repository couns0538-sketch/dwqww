#!/usr/bin/env bash
# M3: build the per-switch and combined exes for both recipes from the current tree, then run the lock identity
# check (uci_check.py --full, Threads 1) and the FMA count on each. OFF and O2 of the same tree are the M1-fix exes
# (forge_r5b_{off,o2}_{v3,z5}_m1fix.exe); this script adds NOZERO, SPEEDSTACK and N2 (= all three switches).
# usage: bash opus_r5/r5b/tools/build_m3.sh <src_dir> <tag>     (exes: F:\opus_scratch\r5\r5b\exe\forge_r5b_<sw>_<r>_<tag>.exe)
# Thread budget: builds JOBS=3 one at a time, then identity checks 3 at once (1 thread each).
set -euo pipefail
SRC=$1; TAG=$2
E=/f/opus_scratch/r5/r5b/exe
L="$SRC/opus_r5/r5b/logs"
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
declare -A FL=([nozero]="-DFORGE_NOZERO_MOVE_BUFFERS=1" [speedstack]="-DFORGE_SPEEDSTACK=1"
               [n2]="-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1")
names=()
for r in z5 v3; do
  rec=$([ $r = z5 ] && echo znver5 || echo v3)
  for sw in nozero speedstack n2; do
    n=${sw}_${r}_${TAG}
    # shellcheck disable=SC2086
    RECIPE=$rec bash "$SRC/opus_r5/r5b/tools/build_r5b.sh" "$SRC" "$E/forge_r5b_$n.exe" ${FL[$sw]} > "$L/build_$n.log" 2>&1
    echo "$n: $(grep -c -i warning "$L/build_$n.log") warnings, $(grep 'FMA' "$L/build_$n.log")"
    names+=("$n")
  done
done
run_id() { nice -n 10 "$PY" -I -B "$LA/2_build/uci_check.py" "$E/forge_r5b_$1.exe" --full 2>&1 | tr -d '\r' > "$L/identity_$1.log"; }
i=0
for n in "${names[@]}"; do
  run_id "$n" &
  i=$((i + 1))
  if [ $((i % 3)) -eq 0 ]; then wait; fi
done
wait
for n in "${names[@]}"; do echo "$n identity: $(tail -1 "$L/identity_$n.log")"; done
