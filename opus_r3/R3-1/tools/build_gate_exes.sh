#!/bin/bash
# Build the R3-3 gate executables from the opus-r3-stack worktree (PC lock recipe) into F:\opus_scratch\r3\exe.
# usage: build_gate_exes.sh [worktree]   -> exe/forge_r3_<name>.exe + exe/EXES.txt (name | flags | sha256 | head)
set -u
WT=${1:-/f/opus_scratch/worktrees/opus_r3_stack}
OUT=/f/opus_scratch/r3/exe
mkdir -p $OUT
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
BUILD=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh
HEAD=$(git -C "$WT" rev-parse --short=8 HEAD)
: > $OUT/EXES.txt
b() { # name flags...
  local name=$1; shift
  nice -n 19 bash $BUILD "$WT" "$OUT/forge_r3_$name.exe" "$@" > "$OUT/forge_r3_$name.build.log" 2>&1 || { echo "BUILD FAILED $name"; return 1; }
  local fma; fma=$(grep -o 'count: [0-9]*' "$OUT/forge_r3_$name.build.log" | cut -d' ' -f2)
  local id; id=$(nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$OUT/forge_r3_$name.exe" --full 2>&1 | tail -1)
  echo "forge_r3_$name.exe | ${*:-default} | $(sha256sum "$OUT/forge_r3_$name.exe" | cut -d' ' -f1) | $HEAD | FMA $fma | $id" | tee -a $OUT/EXES.txt
}
b base
cp "$OUT/forge_r3_base.exe" "$OUT/forge_r3_stack.exe"
echo "forge_r3_stack.exe | copy of forge_r3_base.exe (the default build carries every runtime option) | $(sha256sum "$OUT/forge_r3_stack.exe" | cut -d' ' -f1) | $HEAD" | tee -a $OUT/EXES.txt
b o2 -DFORGE_NNUE_O2=1
b nozero -DFORGE_NOZERO_MOVE_BUFFERS=1
b ttprefetch -DFORGE_S13_TT_CHILD_PREFETCH=1
b speedstack -DFORGE_SPEEDSTACK=1
b lazyacc -DFORGE_NNUE_LAZY_ACC=1
b int16 -DFORGE_NNUE_INT16=1
