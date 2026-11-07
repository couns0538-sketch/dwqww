#!/usr/bin/env bash
# build_harness.sh - plain g++ build of int8_evaldiff against a gate tree (own code, 2026-11-06). Not a gate exe.
# usage: bash build_harness.sh <gate tree> <out dir> [-DNAME=V ...]
# Lock flags (build_variants.ps1 line 143) at -O3, every src/*.cpp of the tree (uci.cpp's main renamed) + the harness.
# Placement comes from the caller (the session runs at affinity 0xF, Idle; children inherit both).
set -u
[ $# -ge 2 ] || { echo "usage: build_harness.sh <gate tree> <out dir> [-D...]"; exit 2; }
T="$1"; O="$2"; shift 2
H="$(cd "$(dirname "$0")" && pwd)/int8_evaldiff.cpp"
[ -e "$O" ] && { echo "build_harness: $O exists (never overwritten)"; exit 2; }
mkdir -p "$O" || exit 2
export PATH="/c/msys64/ucrt64/bin:$PATH"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Wall -Wextra $*"
cd "$T" || exit 2
for f in src/*.cpp; do
  extra=""; [ "$(basename "$f")" = uci.cpp ] && extra="-Dmain=forge_uci_main_unused"
  g++ $FLAGS $extra -Iinclude -c "$f" -o "$O/$(basename "$f" .cpp).o" > "$O/build.log" 2>&1 || { cat "$O/build.log"; exit 1; }
done
g++ $FLAGS -Iinclude -c "$H" -o "$O/int8_evaldiff.o" >> "$O/build.log" 2>&1 || { cat "$O/build.log"; exit 1; }
g++ $FLAGS -static "$O"/*.o -o "$O/int8_evaldiff.exe" >> "$O/build.log" 2>&1 || { cat "$O/build.log"; exit 1; }
echo "build_harness: $O/int8_evaldiff.exe $(sha256sum "$O/int8_evaldiff.exe" | cut -c1-16)"
