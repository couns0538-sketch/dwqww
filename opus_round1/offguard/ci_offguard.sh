#!/usr/bin/env bash
# OFF-path guard for the default-OFF engine options added in the Sol-leftover round, on a quiet GitHub runner.
# For each option branch: build its engine commit with the box flags (g++-14, CMake Release), check AL1 identity with
# the option off (uci_check --full: 5 bench depths, perft5, kiwipete), record hot-function sizes, and run a paired ABBA
# NPS A/B (nps_ab.py, fresh processes, 10 runs per side, bench d16 d20, nodes must match) against the lock 294dbed.
# usage: opus_round1/offguard/ci_offguard.sh [out_dir]      (used by .github/workflows/opus-offguard-ci.yml)
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/offguard"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOCK=294dbed3a15dfd821aaf9d4edc6e5f62832fd460
# name=engine commit (the branch heads carry the same src/include/CMakeLists.txt; checked when this file was written)
ARMS="A1_HistRework=a8b63aae341a1ecfd43372b6ba83075e71c65b1f SA2_NnueInt16=d2301c511abb2a8d724d5f81da7db2debbe03806 S41_NetScale=5a19786353f4dcfb4857fea9cddd4935ad8bb7a3"
status=0
build() {  # build <name> <commit>
  local src="$OUT/src_$1" bld="$OUT/build_$1"
  mkdir -p "$src" && git -C "$ROOT" archive "$2" | tar -x -m -C "$src" || { echo "archive $2 failed"; exit 1; }
  cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_$1.log" 2>&1 || { tail -30 "$OUT/configure_$1.log"; exit 1; }
  cmake --build "$bld" -j"$(nproc)" --target forge > "$OUT/build_$1.log" 2>&1 || { tail -50 "$OUT/build_$1.log"; exit 1; }
  echo "$1 commit $2 forge sha256 $(sha256sum "$bld/forge" | cut -d' ' -f1)" | tee -a "$OUT/builds.log"
}
build lock "$LOCK"
for arm in $ARMS; do build "${arm%%=*}" "${arm##*=}"; done
{ for t in lock $(for arm in $ARMS; do echo "${arm%%=*}"; done); do
    nm -S --size-sort -C "$OUT/build_$t/forge" | grep -E ' forge::(Worker::(search|qsearch|static_evaluate)|nnue::(update|evaluate|refresh))\(' | sed "s/^/$t /"
  done; } > "$OUT/hot_function_sizes.log" 2>&1
for arm in $ARMS; do
  n=${arm%%=*}
  python3 "$CI/uci_check.py" "$OUT/build_$n/forge" --full > "$OUT/identity_$n.log" 2>&1
  if grep -q '^ALL OK' "$OUT/identity_$n.log"; then echo "$n identity (option off): ALL OK"; else echo "$n identity FAILED"; status=1; fi
done
for arm in $ARMS; do
  n=${arm%%=*}
  python3 "$JOB/nps_ab.py" "$OUT/build_lock/forge" "$OUT/build_$n/forge" 10 16 20 > "$OUT/nps_lock_vs_$n.log" 2>&1 || { echo "nps_ab failed for $n"; status=1; }
  grep -E 'B/A' "$OUT/nps_lock_vs_$n.log" | sed "s/^/$n: /"
done
grep -l 'NODE MISMATCH' "$OUT"/nps_*.log && { echo "node mismatch in an NPS A/B"; status=1; }
echo "ci_offguard status=$status"
exit $status
