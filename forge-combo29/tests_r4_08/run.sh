#!/bin/bash
# Build and run the r4-08 checks with address and undefined sanitizers.
# Compile definitions match forge-combo29/CMakeLists.txt. This script does not
# edit that file and does not change any FORGE_* value.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
build="${TMPDIR:-/tmp}/r4-08-build"
mkdir -p "$build"

defs=(
  -DNDEBUG
  -DFORGE_NNUE_HIDDEN=256
  -DFORGE_NNUE_WEIGHTS="\"$root/src/nnue_weights.inc\""
  -DFORGE_EXPOSE_TUNABLES=1
  -DFORGE_SPD_TT_NOTLS=1
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2
  -DFORGE_SEARCH_SPEED2=1
  -DFORGE_SPD_PREFETCH_EARLY=1
  -DFORGE_SPD_SLIDER_PEXT=1
  -DFORGE_SPD_NNUE_ZMM=1
)
flags=(
  -std=c++20 -O3 -g
  -fsanitize=address,undefined -fno-omit-frame-pointer
  -ffp-contract=off -fno-fast-math -march=x86-64-v4
  -I"$root/include"
  "${defs[@]}"
)

sources=(bitboard board eval eval_params nnue search)
pids=()
for src in "${sources[@]}"; do
  g++ "${flags[@]}" -c "$root/src/$src.cpp" -o "$build/$src.o" &
  pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do
  wait "$pid" || status=1
done
if [[ "$status" -ne 0 ]]; then
  echo "FAIL compile" >&2
  exit 1
fi

g++ "${flags[@]}" "$root/tests_r4_08/r4_08_test.cpp" \
  "$build/bitboard.o" "$build/board.o" "$build/eval.o" "$build/eval_params.o" \
  "$build/nnue.o" "$build/search.o" -lpthread -o "$build/r4_08_test"

export ASAN_OPTIONS="${ASAN_OPTIONS:-halt_on_error=1:detect_leaks=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-halt_on_error=1:print_stacktrace=1}"
"$build/r4_08_test"
