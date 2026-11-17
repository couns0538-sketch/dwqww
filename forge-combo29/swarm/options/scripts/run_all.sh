#!/usr/bin/env bash
# Reproduce the whole audit from the audit base commit.
#
# Every step's exit status is checked explicitly. A pipeline's status is the
# last command's, so nothing here reads `$?` after a pipe.
#
# Usage:  ./run_all.sh <out-dir> [--with-sanitizer]
set -euo pipefail

OUT=${1:?usage: run_all.sh <out-dir> [--with-sanitizer]}
WITH_SAN=${2:-}

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE_COMMIT=6b98f217
REPO=${FORGE_REPO:-/agent/repos/dwqww}
WORK=${FORGE_WORK:-/home/ubuntu/work}
SRC="$WORK/base/forge-combo29"

step() { printf '\n=== %s\n' "$*"; }

step "materialise the audit base commit at $BASE_COMMIT"
if [ ! -d "$SRC" ]; then
  mkdir -p "$WORK"
  git -C "$REPO" worktree add --detach "$WORK/base" "$BASE_COMMIT"
fi
git -C "$WORK/base" rev-parse HEAD | tee "$OUT/base-commit.txt"

step "release build (GCC, the toolchain the lock was verified with)"
mkdir -p "$WORK/build-base"
cmake -S "$SRC" -B "$WORK/build-base" \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release >"$WORK/build-base/cmake.log" 2>&1
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake --build "$WORK/build-base" -j"$(nproc)" >"$WORK/build-base/build.log" 2>&1
echo "built $WORK/build-base/forge"

step "confirm the honesty pins BEFORE any measurement"
# A switch that moved a pin would be the first finding, so the pins are checked
# on the clean build and the result is written beside the audit.
"$HERE/check_pins.sh" "$WORK/build-base/forge" | tee "$OUT/pins.txt"

step "corpus"
mkdir -p "$OUT/corpus"
python3 "$HERE/make_corpus.py" --root "$SRC" --out "$OUT/corpus" | tee "$OUT/corpus/corpus.json.txt"
# The prover judged the corpus; its own self-test runs before it is trusted.
python3 "$HERE/prover_selftest.py" | tee "$OUT/corpus/prover-selftest.txt"

step "calibrate the mate wire format (a measurement, not a convention)"
python3 "$HERE/calibrate_mate_format.py" \
  "$WORK/build-base/forge" "$WORK/brute_mate" "$OUT/corpus/mates30.json" \
  | tee "$OUT/corpus/mate-format.txt"

step "baseline arm"
python3 "$HERE/audit.py" --engine "$WORK/build-base/forge" --corpus "$OUT/corpus" \
  --out "$OUT/audit-base" --only BASELINE | tee "$OUT/audit-base.log"

step "eighteen arms, one switch on each"
python3 "$HERE/audit.py" --engine "$WORK/build-base/forge" --corpus "$OUT/corpus" \
  --out "$OUT/audit-switches" --baseline "$OUT/audit-base/audit.json" \
  | tee "$OUT/audit-switches.log"

if [ "$WITH_SAN" = "--with-sanitizer" ]; then
  step "sanitizer: ASan+UBSan, runtime proved live, planted faults proved caught"
  bash "$HERE/run_sanitizer.sh" "$OUT"
fi

step "table"
python3 "$HERE/report.py" --audit "$OUT/audit-switches/audit.json" \
  --baseline "$OUT/audit-base/audit.json" --sanitizer-dir "$OUT/sanitizer" \
  --out "$OUT/table.md" | tee "$OUT/table.txt"

echo
echo "done. evidence in $OUT"
