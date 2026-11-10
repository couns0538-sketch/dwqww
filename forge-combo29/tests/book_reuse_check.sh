#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-book-tests-$$"
mkdir -p "$out"
trap 'rm -rf "$out"' EXIT
flags=(-std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -Iinclude)
export ASAN_OPTIONS=detect_leaks=0
for mode in 0 1; do
  g++ "${flags[@]}" -DFORGE_BOOK_LEGAL_REUSE="$mode" tests/book_legal_reuse.cpp src/board.cpp src/bitboard.cpp src/book.cpp -o "$out/book-$mode"
  "$out/book-$mode"
done
g++ "${flags[@]}" tests/book_board_audit.cpp src/board.cpp src/bitboard.cpp -o "$out/board"
"$out/board"
