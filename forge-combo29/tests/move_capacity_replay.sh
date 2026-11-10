#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-move-capacity-replay-$$"
trap 'rm -f "$out"' EXIT
for no_zero in 0 2; do
 for witnesses in 0 1; do
 for king_lines in 0 1; do
  "${CXX:-g++-14}" -std=c++20 -O1 -g -DNDEBUG -fsanitize=address,undefined -fno-omit-frame-pointer \
   -DFORGE_SPD_LEGAL_WITNESSES="$witnesses" -DFORGE_SPD_KING_LINES="$king_lines" -DFORGE_SPD_NO_ZERO_MOVELISTS="$no_zero" \
   -Iinclude tests/move_capacity_replay.cpp src/board.cpp src/bitboard.cpp -o "$out"
  ASAN_OPTIONS=detect_leaks=0 "$out" tests/move_capacity_maxima.txt
 done
done
done
