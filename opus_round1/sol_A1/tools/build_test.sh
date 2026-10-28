#!/usr/bin/env bash
# Direct g++ build of forge_hist_rework_tests (used for fast iteration and by mutation_check.sh).
# usage: build_test.sh <src_root> <out_exe> [extra g++ flags...]
# MSYS2 ucrt64 g++ 15.2, -O2 with asserts on, the box NNUE/FP flags, static. Run it under `nice -n 19`.
set -euo pipefail
SRC=$1; OUT=$2; shift 2
GPP=/c/msys64/ucrt64/bin/g++.exe
export PATH=/c/msys64/ucrt64/bin:$PATH
cd "$SRC"
CORE="src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp"
"$GPP" -std=c++20 -O2 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -static -pthread \
  -Iinclude "$@" $CORE tests/hist_rework_tests.cpp -o "$OUT"
echo "built $OUT"
