#!/usr/bin/env bash
# Build everything the benchvalid seat measures. Run from a clean checkout.
#   export BENCHVALID_WORK=/tmp/bv
#   scripts/build_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${BENCHVALID_WORK:-$PWD/benchvalid-work}"
BASE_COMMIT="${BENCHVALID_BASE:-6b98f217}"
export BENCHVALID_WORK="$WORK"

mkdir -p "$WORK"
if [ ! -d "$WORK/base/forge-combo29" ]; then
  git worktree add "$WORK/base" "$BASE_COMMIT" --detach
fi

# 1. the release build the pins are read from
cmake -S "$WORK/base/forge-combo29" -B "$WORK/build" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 >/dev/null
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build "$WORK/build" -j"$(nproc)" >/dev/null

# 2. the instrumented probes (same defines, same ISA)
bash "$HERE/build_probe.sh" "$WORK/base" "$WORK/bin/benchprobe"  "$HERE/benchprobe.cpp"
bash "$HERE/build_probe.sh" "$WORK/base" "$WORK/bin/orderprobe"  "$HERE/orderprobe.cpp"

# 3. the coverage build, only needed by bench_coverage.py
cmake -S "$WORK/base/forge-combo29" -B "$WORK/cov" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
      -DCMAKE_CXX_FLAGS="--coverage -fprofile-arcs -ftest-coverage" \
      -DCMAKE_EXE_LINKER_FLAGS="--coverage" >/dev/null
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build "$WORK/cov" -j"$(nproc)" >/dev/null

echo "built: $WORK/build/forge"
echo "       $WORK/bin/benchprobe  $WORK/bin/orderprobe  $WORK/cov/forge"
