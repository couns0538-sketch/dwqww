#!/usr/bin/env bash
# Sanitizer runs: one per switch, each proved live.
#
# The clean binary is built from the audited sources with no test hooks. The
# control binary adds one extra translation unit carrying a deliberate
# heap-buffer-overflow and a deliberate signed-integer overflow. Both must be
# caught, or the clean run proves nothing and this script exits non-zero.
set -euo pipefail

OUT=${1:?usage: run_sanitizer.sh <out-dir>}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=${FORGE_REPO:-/agent/repos/dwqww}
WORK=${FORGE_WORK:-/home/ubuntu/work}
SRC="$WORK/base/forge-combo29"
SAN_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1"

step() { printf '\n--- %s\n' "$*"; }

step "sanitized clean build"
mkdir -p "$WORK/build-asan"
cmake -S "$SRC" -B "$WORK/build-asan" \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_FLAGS="$SAN_FLAGS" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
  >"$WORK/build-asan/cmake.log" 2>&1
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake --build "$WORK/build-asan" -j"$(nproc)" >"$WORK/build-asan/build.log" 2>&1

step "sanitized control build (planted faults)"
mkdir -p "$WORK/build-asan-planted"
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 /usr/bin/g++ -std=c++20 $SAN_FLAGS \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 \
  -DFORGE_NNUE_WEIGHTS="\"$SRC/src/nnue_weights.inc\"" \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -I"$SRC/include" "$SRC"/src/*.cpp "$HERE/planted_fault.cpp" \
  -pthread -o "$WORK/build-asan-planted/forge-planted"

for SWITCH in ContHist4PlyRead NonPawnCorrection LmrDeeperShallower EvalRule50Damp \
              ThreatHistory LmrSignedCorrection LmrLateParentRelief HindsightDepth \
              NullThreatVerify NullSeeVeto AspCappedReopen AspArmLate EvasionOrdering \
              DeadMaterial QuietExtinction TmFinishIteration TmNodeShare SoundMatePruning; do
  step "sanitizer: $SWITCH"
  mkdir -p "$OUT/sanitizer/$SWITCH"
  python3 "$HERE/sanitizer.py" \
    --clean "$WORK/build-asan/forge" --clean-build "$WORK/build-asan" \
    --planted "$WORK/build-asan-planted/forge-planted" \
    --corpus "$OUT/corpus" --out "$OUT/sanitizer/$SWITCH" \
    --option "$SWITCH=true" \
    | tee "$OUT/sanitizer/$SWITCH/report.txt"
done

step "sanitizer: baseline (no switch)"
mkdir -p "$OUT/sanitizer/BASELINE"
python3 "$HERE/sanitizer.py" \
  --clean "$WORK/build-asan/forge" --clean-build "$WORK/build-asan" \
  --planted "$WORK/build-asan-planted/forge-planted" \
  --corpus "$OUT/corpus" --out "$OUT/sanitizer/BASELINE" \
  | tee "$OUT/sanitizer/BASELINE/report.txt"
