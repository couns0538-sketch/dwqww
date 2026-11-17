#!/bin/bash
# Build the arms of the audit.
#
#   clean  -- the engine source as committed on this branch. This is what the
#             pins gate: bench 11/13/16 and perft 5 must match exactly.
#   probe  -- same source + -DFORGE_PRUNE_PROBE=ON. Passive counters and ablation
#             switches. With no ablation set, its node counts MUST equal the
#             clean arm's; check_probe_identity.py proves that, and a failure
#             there invalidates every count taken with the probe.
#   base   -- the AUDIT BASE itself (6b98f217), rebuilt from pristine source, used
#             as the third arm of the identity check. It is built from git rather
#             than shipped as a committed binary: a binary in the tree is a blob
#             nobody can reproduce, and the brief commits no binaries. Building it
#             here is also a stronger check, because it proves the branch's source
#             really is the audit base plus the probe and nothing else.
#
# The g++ recipe is the brief's: /usr/bin/g++ with LIBRARY_PATH pinned to gcc 13,
# because /usr/bin/c++ is clang 18 with a broken header path.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ -> pruning/ -> swarm/ -> forge-combo29/
ENGINE="$(cd "$HERE/../../.." && pwd)"
REPO="$(cd "$ENGINE/.." && pwd)"
BUILD_BASE="$(cd "$HERE/.." && pwd)/build"
AUDIT_BASE_COMMIT="${AUDIT_BASE_COMMIT:-6b98f217}"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

common_cmake=(
  -DCMAKE_CXX_COMPILER=/usr/bin/g++
  -DCMAKE_BUILD_TYPE=Release
  -DFORGE_MARCH=x86-64-v4
)

build_one() {
  local src="$1"; shift
  local dir="$1"; shift
  local name="$1"; shift
  mkdir -p "$dir"
  ( cd "$dir" && cmake "$src" "${common_cmake[@]}" "$@" > cmake.log 2>&1 && make -j"$(nproc)" > make.log 2>&1 )
  echo "built $dir/forge  ($name)"
}

# The audit base, materialised from git into a temporary tree. Requires the base
# commit to be present locally (it is on any clone that has this branch's history
# only if the base is an ancestor; otherwise fetch it or set AUDIT_BASE_COMMIT).
build_base() {
  local out="$BUILD_BASE/base"
  if [ -d "$out" ] && [ -x "$out/forge" ]; then
    echo "reusing $out/forge  (base)"
    return 0
  fi
  if ! git -C "$REPO" cat-file -e "${AUDIT_BASE_COMMIT}^{commit}" 2>/dev/null; then
    echo "cannot build the base arm: commit $AUDIT_BASE_COMMIT is not in this clone." >&2
    echo "Fetch it (git fetch origin $AUDIT_BASE_COMMIT) or set AUDIT_BASE_COMMIT." >&2
    return 3
  fi
  local tmp
  tmp="$(mktemp -d)"
  git -C "$REPO" archive "$AUDIT_BASE_COMMIT" forge-combo29 | tar -x -C "$tmp"
  build_one "$tmp/forge-combo29" "$out" "base $AUDIT_BASE_COMMIT"
  rm -rf "$tmp"
}

case "${1:-all}" in
  clean) build_one "$ENGINE" "$BUILD_BASE/clean" "clean" ;;
  probe) build_one "$ENGINE" "$BUILD_BASE/probe" "probe" -DFORGE_PRUNE_PROBE=ON ;;
  base)  build_base ;;
  all)
    build_one "$ENGINE" "$BUILD_BASE/clean" "clean"
    build_one "$ENGINE" "$BUILD_BASE/probe" "probe" -DFORGE_PRUNE_PROBE=ON
    build_base
    ;;
  *) echo "usage: $0 [clean|probe|base|all]" >&2; exit 2 ;;
esac

