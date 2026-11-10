#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-/tmp/forge-worker-exception}"
for latch in 0 1; do
  "${CXX:-g++-14}" -std=c++20 -O2 -pthread -static-libstdc++ -ffp-contract=off -fno-fast-math \
    -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
    -DFORGE_FIX_SMP_EXCEPTIONS=1 -DFORGE_FIX_SMP_STOP_LATCH="$latch" \
    -Iinclude tests/thread_exception_workers.cpp src/search.cpp src/board.cpp src/bitboard.cpp \
    src/eval.cpp src/eval_params.cpp src/nnue.cpp \
    -Wl,--wrap=pthread_create -Wl,--wrap=pthread_join -o "$out"
  "$out"
  "$out" helper
done
