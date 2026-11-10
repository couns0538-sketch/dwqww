#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-movegen-focused-$$"
trap 'rm -f "$out"' EXIT
for king_lines in 0 1; do
  "${CXX:-g++-14}" -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -DFORGE_SPD_KING_LINES="$king_lines" -Iinclude tests/movegen_focused_corners.cpp src/board.cpp src/bitboard.cpp -o "$out"
  ASAN_OPTIONS=detect_leaks=0 "$out"
done
