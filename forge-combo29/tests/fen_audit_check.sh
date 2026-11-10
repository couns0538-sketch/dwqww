#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-fen-audit-$$"
mkdir -p "$out"
trap 'rm -rf "$out"' EXIT
flags=(-std=c++20 -O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer -DFORGE_NNUE_HIDDEN=256 -Iinclude)
"${CXX:-g++-14}" "${flags[@]}" tests/fen_audit_board.cpp src/board.cpp src/bitboard.cpp -o "$out/board"
ASAN_OPTIONS=detect_leaks=0 "$out/board"
"${CXX:-g++-14}" "${flags[@]}" tests/fen_audit_uci.cpp src/{search,board,bitboard,eval,eval_params,nnue,book}.cpp -o "$out/uci"
ASAN_OPTIONS=detect_leaks=0 "$out/uci"
