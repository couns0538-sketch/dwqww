#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-/tmp/forge-thread-exception}"
shift || true
"${CXX:-g++-14}" -std=c++20 -O2 -pthread -static-libstdc++ -ffp-contract=off -fno-fast-math \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Iinclude "$@" tests/thread_exception.cpp src/search.cpp src/board.cpp src/bitboard.cpp \
  src/eval.cpp src/eval_params.cpp src/nnue.cpp \
  -Wl,--wrap=pthread_create -o "$out"
"$out"
