#!/bin/bash
# Finding 1 checks. A failing compile, a sanitizer report, or a failed assertion
# exits non-zero. AddressSanitizer and UBSan do not prove the absence of a race;
# the concurrent Board construction runs under ThreadSanitizer.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
out="${TMPDIR:-/tmp}/forge-r4-06"
mkdir -p "$out"

cxx="${CXX:-g++}"
common=(
  -std=c++20
  -O2
  -g
  -fno-omit-frame-pointer
  -ffp-contract=off
  -fno-fast-math
  -pthread
  -Iforge-combo29/include
  -DFORGE_NNUE_HIDDEN=256
  -DFORGE_SPD_TT_NOTLS=1
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2
  -DFORGE_SEARCH_SPEED2=1
  -DFORGE_SPD_PREFETCH_EARLY=1
)

export TSAN_OPTIONS="${TSAN_OPTIONS:-halt_on_error=1:exitcode=66}"
export ASAN_OPTIONS="${ASAN_OPTIONS:-halt_on_error=1:abort_on_error=1:detect_leaks=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-halt_on_error=1:abort_on_error=1:print_stacktrace=1}"

echo "TSan PEXT=0 (magic search, first initialization)"
"$cxx" "${common[@]}" -fsanitize=thread -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -march=x86-64-v3 \
  forge-combo29/tests_r4_06/concurrent_board_init.cpp \
  forge-combo29/src/bitboard.cpp \
  forge-combo29/src/board.cpp \
  -o "$out/concurrent_board_init_tsan_pext0"
"$out/concurrent_board_init_tsan_pext0"

echo "TSan PEXT=1 (lock slider tables, first initialization)"
"$cxx" "${common[@]}" -fsanitize=thread -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=0 \
  -march=x86-64-v3 \
  forge-combo29/tests_r4_06/concurrent_board_init.cpp \
  forge-combo29/src/bitboard.cpp \
  forge-combo29/src/board.cpp \
  -o "$out/concurrent_board_init_tsan_pext1"
"$out/concurrent_board_init_tsan_pext1"

weights="$root/forge-combo29/src/nnue_weights.inc"
echo "ASan+UBSan: 200 depth-10 searches"
"$cxx" "${common[@]}" -fsanitize=address,undefined -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -march=x86-64-v4 \
  -DFORGE_NNUE_WEIGHTS="\"$weights\"" \
  forge-combo29/tests_r4_06/depth10_legal.cpp \
  forge-combo29/src/bitboard.cpp \
  forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp \
  forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp \
  forge-combo29/src/search.cpp \
  -o "$out/depth10_legal_asan"
"$out/depth10_legal_asan"

echo "PASS r4-06 checks"
