#!/usr/bin/env bash
# S-IT follow-up planted-bug check: each mutant goes to a NEW folder <out>/mut_<name> (mutate_sit.py), only the
# patched translation unit is recompiled (other objects copied from <base_obj>), and the unit test must FAIL.
# usage: run_mutants.sh <worktree> <out_dir> <base_obj_dir> <mutant>...
set -uo pipefail
WT=$1; OUT=$2; BASEOBJ=$3; shift 3
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
caught=0; total=0
for m in "$@"; do
  dir="$OUT/mut_$m"
  total=$((total + 1))
  if ! "$PY" -I -B "$WT/opus_round1/sol_SIT/mutate_sit.py" "$WT" "$dir" "$m" > /dev/null; then
    echo "mutant $m: GENERATION FAILED"; continue
  fi
  changed=""
  for f in src/board.cpp src/search.cpp; do cmp -s "$WT/$f" "$dir/$f" || changed="$changed $f"; done
  mkdir -p "$dir/obj" && cp "$BASEOBJ"/*.o "$dir/obj/"
  if ! bash "$HERE/build_unit_tests.sh" "$dir" "$dir/obj" "$dir/t.exe" $changed > "$dir/build.log" 2>&1; then
    echo "mutant $m: BUILD FAILED"; tail -5 "$dir/build.log"; continue
  fi
  nice -n 19 "$dir/t.exe" > "$dir/run.log" 2>&1; rc=$?
  fails=$(grep -c '^FAIL' "$dir/run.log")
  verdict=$([ "$rc" -ne 0 ] && [ "$fails" -gt 0 ] && echo CAUGHT || echo "NOT CAUGHT")
  [ "$verdict" = CAUGHT ] && caught=$((caught + 1))
  echo "mutant $m ($changed ): rc=$rc FAIL lines $fails -> $verdict"
  grep '^FAIL' "$dir/run.log" | head -3 | cut -c1-200
done
echo "caught $caught/$total"
