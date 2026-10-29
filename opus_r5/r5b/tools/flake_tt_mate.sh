#!/usr/bin/env bash
# R5B CI note: failure rate of tests/tt_mate_tb_tests.cpp (its Threads 2 shared-TT mate check failed in two opus-ci
# jobs) for the base forge-bundle-int b7c1772 and for this branch's head, built the same way (box flags x86-64-v3,
# -O3 -DNDEBUG, the forge_core sources + the test, static) and run RUNS times each, sequentially (the test uses at
# most 2 threads), at BelowNormal.
# usage: bash opus_r5/r5b/tools/flake_tt_mate.sh <worktree> <out_dir> [RUNS=40]
set -uo pipefail
WT=$1; OUT=$2; RUNS=${3:-40}
export PATH=/c/msys64/ucrt64/bin:$PATH
mkdir -p "$OUT/base_src"
git -C "$WT" -c core.autocrlf=false archive b7c17722 src include tests | tar -x -C "$OUT/base_src"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread"
CORE="src/bitboard.cpp src/board.cpp src/book.cpp src/datagen.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp"
for side in base head; do
  src=$([ "$side" = base ] && echo "$OUT/base_src" || echo "$WT")
  # shellcheck disable=SC2086
  (cd "$src" && nice -n 10 g++ $FLAGS -Iinclude tests/tt_mate_tb_tests.cpp $CORE -static -o "$OUT/tt_mate_tb_$side.exe") \
    || { echo "build $side failed"; exit 1; }
  fails=0
  for i in $(seq 1 "$RUNS"); do
    if ! nice -n 10 "$OUT/tt_mate_tb_$side.exe" > "$OUT/run_${side}_$i.log" 2>&1; then
      fails=$((fails + 1)); echo "$side run $i FAILED: $(grep -m1 '^FAIL' "$OUT/run_${side}_$i.log")"
    fi
  done
  echo "$side ($(sha256sum "$OUT/tt_mate_tb_$side.exe" | cut -c1-16)): $fails of $RUNS runs failed"
done
