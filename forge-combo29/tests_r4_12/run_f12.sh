#!/usr/bin/env bash
# Address + undefined sanitizer check for finding 12.
# Compile definitions match forge-combo29/CMakeLists.txt. This script does not
# edit that file and does not change those definitions.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="${TMPDIR:-/tmp}/r4_12"
mkdir -p "$out"

flags=(
  -std=c++20 -pthread
  -ffp-contract=off -fno-fast-math -march=x86-64-v4
  -DFORGE_EXPOSE_TUNABLES=1
  -DFORGE_SPD_TT_NOTLS=1
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2
  -DFORGE_SEARCH_SPEED2=1
  -DFORGE_SPD_PREFETCH_EARLY=1
  -DFORGE_SPD_SLIDER_PEXT=1
  -DFORGE_SPD_NNUE_ZMM=1
  -DFORGE_NNUE_HIDDEN=256
  -DFORGE_NNUE_WEIGHTS="\"$root/src/nnue_weights.inc\""
  -I"$root/include" -I"$root/src"
  -UNDEBUG
  -O1 -g -fno-omit-frame-pointer
  -fsanitize=address,undefined
  -fno-sanitize-recover=address,undefined
)

srcs=(bitboard.cpp board.cpp book.cpp eval.cpp eval_params.cpp nnue.cpp search.cpp)
for src in "${srcs[@]}"; do
  g++ "${flags[@]}" -c "$root/src/$src" -o "$out/${src%.cpp}.o"
done
g++ "${flags[@]}" "$root/tests_r4_12/empty_move_uci.cpp" "$out"/*.o -o "$out/empty_move_uci"

export ASAN_OPTIONS="${ASAN_OPTIONS:-halt_on_error=1:abort_on_error=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-halt_on_error=1:abort_on_error=1:print_stacktrace=1}"
"$out/empty_move_uci"
