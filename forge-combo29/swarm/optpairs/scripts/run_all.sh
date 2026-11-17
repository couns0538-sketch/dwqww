#!/usr/bin/env bash
# Re-run everything in this folder, in dependency order, from a clean build.
#
#   ./run_all.sh            # build, pins, fixtures, then every grid
#
# Assumes the brief's build recipe. The v3 and TSan binaries are only needed by
# pairs 6 and 7; if they are missing those scripts fail loudly rather than
# silently reporting a null.
set -eu
cd "$(dirname "$0")"

FORGE_SRC=${FORGE_SRC:-../../../forge-combo29}
AUDIT_BUILD=${AUDIT_BUILD:-/tmp/build-optpairs}
V3_BUILD=${V3_BUILD:-/tmp/build-v3}
TSAN_BUILD=${TSAN_BUILD:-/tmp/build-tsan}

build() {
  local dir=$1; shift
  mkdir -p "$dir"
  ( cd "$dir" && cmake -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 "$@" "$FORGE_SRC" >/dev/null
    cmake --build . -j"$(nproc)" >/dev/null )
  echo "built $dir/forge"
}

[ -x "$AUDIT_BUILD/forge" ] || build "$AUDIT_BUILD"
[ -x "$V3_BUILD/forge" ]    || build "$V3_BUILD" -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_V3=1"
if [ ! -x "$TSAN_BUILD/forge" ]; then
  build "$TSAN_BUILD" -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_CXX_FLAGS="-fsanitize=thread -g" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread"
fi

echo "== pins"
./pins.sh "$AUDIT_BUILD/forge"

echo "== fixtures"
python3 check_positions.py

echo "== net fixtures"
python3 make_v2_nets.py
python3 make_v3_nets.py

echo "== pairs"
python3 pair2_multipv_threads.py
python3 pair3_hash_multipv_bail.py
python3 pair3b_hash_axis.py
python3 pair5_book.py
python3 pair5b_book_boundary.py
python3 pair5c_variety.py
python3 pair6_threads_nnue.py
python3 pair7_loader.py
python3 pair7b_usennue_eval.py

echo "== clock timing (slow-ish, run alone on an idle box)"
python3 pair4_overhead_floor.py
python3 pair4b_overhead_clocks.py

echo "== threaded Hash grids (slow-ish, run alone on an idle box)"
python3 pair1_hash_threads.py
python3 pair1b_hash_threads_2m.py
python3 pair1c_hash_pressure.py
python3 pair1_pooled.py

echo "== thread sanitizer"
./tsan_planted_race.sh
python3 tsan_soak.py
echo "done"
