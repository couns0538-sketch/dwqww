#!/bin/bash
# Build the audit binary and gate it on the four honesty pins.
# `bench N` is sent on STDIN as a UCI command: `./forge bench 11` as argv prints
# nothing and exits 0 (brief, "The engine and the build").
set -u
cd "$(dirname "$0")/../../.." || exit 1        # forge-combo29/
BUILD=${BUILD:-build-rule50}
EXE=./$BUILD/forge
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 >/dev/null || exit 1
cmake --build "$BUILD" -j4 >/dev/null || exit 1

out=$(printf 'bench 11\nbench 13\nbench 16\ngo perft 5\nquit\n' | "$EXE" 2>&1)
b11=$(echo "$out" | sed -n 's/.*bench depth 11 nodes \([0-9]*\).*/\1/p')
b13=$(echo "$out" | sed -n 's/.*bench depth 13 nodes \([0-9]*\).*/\1/p')
b16=$(echo "$out" | sed -n 's/.*bench depth 16 nodes \([0-9]*\).*/\1/p')
pf5=$(echo "$out" | sed -n 's/^nodes \([0-9]*\)$/\1/p' | tail -1)

echo "bench 11 = $b11 (want 312866)"
echo "bench 13 = $b13 (want 862329)"
echo "bench 16 = $b16 (want 3024920)"
echo "perft  5 = $pf5 (want 4865609)"

[ "$b11" = 312866 ] && [ "$b13" = 862329 ] && [ "$b16" = 3024920 ] && [ "$pf5" = 4865609 ] \
  || { echo "PINS DO NOT MATCH - do not record anything"; exit 2; }
echo "ALL FOUR PINS MATCH"
