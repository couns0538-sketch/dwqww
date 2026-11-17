#!/usr/bin/env bash
# run_all.sh -- rebuild every build this seat's findings rest on, from a clean base
# worktree, and write the raw output of every measurement under evidence/raw/.
#
# Nothing here writes to the repository's engine source: each build is a COPY under
# /tmp, and the instrumentation is applied by scripts/make_lmr_stats.py.
#
# Usage:  bash run_all.sh [/path/to/clean/base/forge-combo29]
#
# Build trap (findings): /usr/bin/c++ is clang 18 with a broken header path; use
# /usr/bin/g++ and LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SWARM="$(cd "$HERE/.." && pwd)"
RAW="$SWARM/evidence/raw"
BASE_SRC="${1:-/tmp/base/forge-combo29}"
GCC=/usr/bin/g++
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
mkdir -p "$RAW"

[ -d "$BASE_SRC" ] || { echo "no such source tree: $BASE_SRC"; exit 1; }

build() { # name srcdir cmakedefs
  local name="$1" src="$2" defs="$3"
  cmake -S "$src" -B "/tmp/bld_$name" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER="$GCC" -DFORGE_MARCH=x86-64-v4 \
        -DCMAKE_CXX_FLAGS="$defs" > "$RAW/cmake_$name.log" 2>&1 || { echo "cmake FAIL $name"; return 1; }
  cmake --build "/tmp/bld_$name" -j4 > "$RAW/build_$name.log" 2>&1 || { echo "build FAIL $name"; return 1; }
  echo "/tmp/bld_$name/forge"
}

pins() { # exe tag
  local exe="$1" tag="$2" out="$RAW/pins_$2.txt"
  : > "$out"
  for c in "bench 11" "bench 13" "bench 16"; do
    printf 'uci\nisready\n%s\nquit\n' "$c" | "$exe" 2>/dev/null | grep -i "bench depth" > /tmp/p.$$
    # read to bench output only; the engine prints the summary line before returning
    printf '%s %s\n' "$c" "$(grep -o 'nodes [0-9]*' /tmp/p.$$ | tail -1)" >> "$out"
  done
  printf 'position startpos\ngo perft 5\n' > /dev/null
  printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | "$exe" 2>/dev/null \
    | grep '^nodes ' | tail -1 | sed 's/^/perft 5 /' >> "$out"
  rm -f /tmp/p.$$
  echo "== pins $tag"; cat "$out"
}

echo "### base (unmodified 6b98f217)"
BASE=$(build base "$BASE_SRC" "") || exit 1
pins "$BASE" base

echo "### instrumented, FORGE_LMR_STATS=0 (the pin gate)"
rm -rf /tmp/src_off && cp -a "$BASE_SRC" /tmp/src_off
cp "$SWARM/scripts/make_lmr_stats.py" /tmp/
python3 /tmp/make_lmr_stats.py /tmp/src_off nocap > "$RAW/instrument_off.txt"
OFF=$(build off /tmp/src_off "-DFORGE_LMR_STATS=0") || exit 1
pins "$OFF" off
echo "sha256 of the flag-off binary vs the unmodified base binary (must match):" | tee "$RAW/binary_identity.txt"
sha256sum "$OFF" "$BASE" | tee -a "$RAW/binary_identity.txt"

echo "### instrumented, FORGE_LMR_STATS=1"
ON=$(build on /tmp/src_off "-DFORGE_LMR_STATS=1") || exit 1
pins "$ON" on

echo "### cap tree (seat 03's ported r15 bare-king patch) + instrumentation"
rm -rf /tmp/src_cap && cp -a "$BASE_SRC" /tmp/src_cap
( cd /tmp/src_cap && patch -p1 < "$SWARM/patches/base_bare_king_on.patch" ) > "$RAW/patch_cap.txt" 2>&1
python3 /tmp/make_lmr_stats.py /tmp/src_cap cap > "$RAW/instrument_cap.txt"
CAPON=$(build capON /tmp/src_cap "-DFORGE_LMR_STATS=1 -DFORGE_FIX_BARE_KING_LMR_CAP=1 -DFORGE_FIX_BARE_KING_ONE_THREAD=0") || exit 1
CAPOFF=$(build capOFF /tmp/src_cap "-DFORGE_LMR_STATS=1 -DFORGE_FIX_BARE_KING_LMR_CAP=0 -DFORGE_FIX_BARE_KING_ONE_THREAD=0") || exit 1
pins "$CAPON" capON
pins "$CAPOFF" capOFF

echo "### the flag-on identity proof: 40 positions, flag off vs flag on"
python3 "$SWARM/scripts/identity40.py" "$OFF" "$ON" "$SWARM/evidence/OG200.fens" \
    --depth 10 --limit 40 --json "$SWARM/evidence/identity40.json" \
    > "$RAW/identity40.txt" 2>&1
tail -3 "$RAW/identity40.txt"

echo "### the 11 lone-king boards, depth 8 and depth 10, all three builds"
for d in 8 10; do
  for b in "$BASE:base" "$CAPON:capON" "$CAPOFF:capOFF"; do
    exe="${b%%:*}"; tag="${b##*:}"
    python3 "$SWARM/scripts/loneking11.py" "$exe" --depth "$d" --json "$SWARM/evidence/loneking_d${d}_${tag}.json" \
      > "$RAW/loneking_d${d}_${tag}.txt" 2>&1
  done
done

echo "### does any counter separate the two counter-cases?"
python3 "$SWARM/scripts/separation.py" "$SWARM/evidence/loneking_d10_capON.json" \
    "$SWARM/evidence/loneking_d10_capOFF.json" > "$RAW/separation_d10.txt" 2>&1
cat "$RAW/separation_d10.txt"

echo "done"
