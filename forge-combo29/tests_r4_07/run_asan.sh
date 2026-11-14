#!/usr/bin/env bash
# Build and run the finding-3 check with address and undefined sanitizers.
# Compile definitions match the existing combo29 lock test recipe (tests_t22 asan).
# This does not edit CMakeLists.txt and does not add a new FORGE_* switch.
set -euo pipefail
cd "$(dirname "$0")/.."
g++ -std=c++20 -O1 -g -pthread \
    -fno-omit-frame-pointer \
    -fsanitize=address,undefined \
    -fno-sanitize-recover=all \
    -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
    -DFORGE_NNUE_HIDDEN=256 \
    -DFORGE_EXPOSE_TUNABLES=1 \
    -DFORGE_SPD_TT_NOTLS=1 \
    -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
    -DFORGE_SEARCH_SPEED2=1 \
    -DFORGE_SPD_PREFETCH_EARLY=1 \
    -DFORGE_SPD_SLIDER_PEXT=0 \
    -DFORGE_SPD_NNUE_ZMM=0 \
    -I include \
    tests_r4_07/go_mate_test.cpp \
    src/bitboard.cpp src/board.cpp src/book.cpp \
    src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp \
    -o /tmp/r4_07_go_mate_asan
/tmp/r4_07_go_mate_asan
