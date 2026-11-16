#!/usr/bin/env bash
# patch_copy.sh — build seat 01's halfmove patch in a SCRATCH copy (nothing committed, base untouched).
set -u
SRC=/agent/repos/base/forge-combo29
DST=/agent/repos/scratch-patch01
P=/agent/repos/dwqww/forge-combo29/swarm/20/job7/seat01.patch.txt
rm -rf "$DST"; mkdir -p "$DST"
cp -r "$SRC"/CMakeLists.txt "$SRC"/include "$SRC"/src "$DST"/
cd "$DST"
echo "=== patch --dry-run with -p1 and fuzz 0:"
patch -p2 --fuzz=0 --dry-run < "$P"
patch -p2 --fuzz=0 < "$P"
echo "=== the changed lines:"
grep -n -A3 'const bool root_drawn' src/search.cpp | head -8
CXX=g++ CC=gcc cmake -S "$DST" -B "$DST/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ > "$DST/cmake.log" 2>&1
cmake --build "$DST/build" -j4 > "$DST/build.log" 2>&1
echo "build exit=$?"
ls -la "$DST/build/forge"
echo "=== honesty pins with the patch applied:"
for b in 11 13 16; do printf "bench $b\nquit\n" | "$DST/build/forge" 2>&1 | grep 'bench depth'; done
printf 'position startpos\ngo perft 5\nquit\n' | "$DST/build/forge" 2>&1 | tail -1
