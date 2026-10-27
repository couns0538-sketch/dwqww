#!/usr/bin/env bash
# S-IT (UCI IntendedThreefold) quiet-runner evidence, used by .github/workflows/opus-sol-sit-ci.yml (opus-ci.yml
# covers release/ASan/TSan ctest). Box flags, g++-14, CMake Release. Adapted from opus-sol-S29's ci_s29.sh.
#   lock (294dbed) and branch builds; branch AL1 identity with the option off (all 5 bench depths, perft5,
#   kiwipete); hot-function sizes (Worker::search, Worker::qsearch) lock vs branch; advisory NPS with
#   nps_ab_opts.py: lock vs branch (option off) and branch off vs on, 10 runs each, bench d16 d20.
# usage: opus_round1/sol_SIT/ci_sit.sh [out_dir]
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/sol_SIT"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
status=0
build() {  # build <src> <dir>
  cmake -S "$1" -B "$2" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_$(basename "$2").log" 2>&1 || exit 1
  cmake --build "$2" -j"$(nproc)" --target forge > "$OUT/build_$(basename "$2").log" 2>&1 || { tail -50 "$OUT/build_$(basename "$2").log"; exit 1; }
}
mkdir -p "$OUT/lock_src" && git -C "$ROOT" archive 294dbed | tar -x -m -C "$OUT/lock_src"
build "$OUT/lock_src" "$OUT/build_lock"
build "$ROOT" "$OUT/build_sit"
python3 "$CI/uci_check.py" "$OUT/build_sit/forge" --full 2>&1 | tee "$OUT/identity_sit_off.log"
grep -q '^ALL OK' "$OUT/identity_sit_off.log" || status=1
{ for t in lock sit; do
    echo "$t forge sha256 $(sha256sum "$OUT/build_$t/forge" | cut -d' ' -f1)"
    nm -S --size-sort -C "$OUT/build_$t/forge" | grep -E ' forge::Worker::(search|qsearch)\(' | sed "s/^/$t /"
  done; } 2>&1 | tee "$OUT/hot_function_sizes.log"
python3 "$JOB/nps_ab_opts.py" "$OUT/build_lock/forge" "$OUT/build_sit/forge" 10 16 20 2>&1 | tee "$OUT/nps_lock_vs_sit_off.log"
python3 "$JOB/nps_ab_opts.py" --opts-a IntendedThreefold=false --opts-b IntendedThreefold=true \
  "$OUT/build_sit/forge" "$OUT/build_sit/forge" 10 16 20 2>&1 | tee "$OUT/nps_sit_off_vs_on.log"
grep -q 'NODE MISMATCH' "$OUT"/nps_*.log && { echo "node mismatch in an NPS A/B"; status=1; }
echo "ci_sit status=$status"
exit $status
