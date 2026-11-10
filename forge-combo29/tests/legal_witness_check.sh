#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-legal-witness-$$"
mkdir -p "$out"
trap 'rm -rf "$out"' EXIT
for witnesses in 0 1; do
 for king_lines in 0 1; do
  "${CXX:-g++-14}" -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -DFORGE_SPD_LEGAL_WITNESSES="$witnesses" -DFORGE_SPD_KING_LINES="$king_lines" \
    -Iinclude tests/legal_witness_unit.cpp src/board.cpp src/bitboard.cpp -o "$out/test"
  ASAN_OPTIONS=detect_leaks=0 "$out/test"
 done
done
