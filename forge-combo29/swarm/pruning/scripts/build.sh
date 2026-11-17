#!/bin/bash
# Build both arms of the audit.
#
#   build_clean.sh   -- the audit base, untouched source. This is what the pins
#                       gate: bench 11/13/16 and perft 5 must match exactly.
#   build_probe.sh   -- same source + -DFORGE_PRUNE_PROBE=ON. Passive counters and
#                       ablation switches. With no ablation set, its node counts
#                       MUST equal the clean build's; check_probe_identity.py
#                       proves that, and a failure there invalidates every count
#                       taken with the probe.
#
# The g++ recipe is the brief's: /usr/bin/g++ with LIBRARY_PATH pinned to gcc 13,
# because /usr/bin/c++ is clang 18 with a broken header path.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ -> pruning/ -> swarm/ -> forge-combo29/
ENGINE="$(cd "$HERE/../../.." && pwd)"
BUILD_BASE="$(cd "$HERE/.." && pwd)/build"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

common_cmake=(
  -DCMAKE_CXX_COMPILER=/usr/bin/g++
  -DCMAKE_BUILD_TYPE=Release
  -DFORGE_MARCH=x86-64-v4
)

build_one() {
  local dir="$1"; shift
  local name="$1"; shift
  mkdir -p "$dir"
  ( cd "$dir" && cmake "$ENGINE" "${common_cmake[@]}" "$@" > cmake.log 2>&1 && make -j"$(nproc)" > make.log 2>&1 )
  echo "built $dir/forge  ($name)"
}

case "${1:-all}" in
  clean) build_one "$BUILD_BASE/clean" "clean" ;;
  probe) build_one "$BUILD_BASE/probe" "probe" -DFORGE_PRUNE_PROBE=ON ;;
  all)
    build_one "$BUILD_BASE/clean" "clean"
    build_one "$BUILD_BASE/probe" "probe" -DFORGE_PRUNE_PROBE=ON
    ;;
  *) echo "usage: $0 [clean|probe|all]" >&2; exit 2 ;;
esac
