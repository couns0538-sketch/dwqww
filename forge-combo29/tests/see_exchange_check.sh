#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-see-$$"
mkdir -p "$out"
trap 'rm -rf "$out"' EXIT
for hoist in 0 1; do
  "${CXX:-g++-14}" -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -DFORGE_SDK_SEE_HOIST="$hoist" -Iinclude tests/see_exchange_audit.cpp src/board.cpp src/bitboard.cpp -o "$out/see"
  ASAN_OPTIONS=detect_leaks=0 "$out/see" all | tee "$out/result-$hoist"
done
cmp "$out/result-0" "$out/result-1"
echo 'PASS SEE_HOIST off/on diagnostic output identical'
