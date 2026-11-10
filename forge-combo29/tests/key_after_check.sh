#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-key-after-$$"
trap 'rm -f "$out"' EXIT
for mode in default alternate; do
  flags=()
  if [[ "$mode" == alternate ]]; then flags=(-DFORGE_SPD_KING_LINES=0 -DFORGE_SPD_NO_ZERO_MOVELISTS=2); fi
  "${CXX:-g++-14}" -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -DFORGE_SPD_PREFETCH_EARLY=1 "${flags[@]}" -Iinclude tests/key_after_audit.cpp src/board.cpp src/bitboard.cpp -o "$out"
  ASAN_OPTIONS=detect_leaks=0 "$out"
done
