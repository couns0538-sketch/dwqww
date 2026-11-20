#!/usr/bin/env bash
# Build a fresh base tree, apply one patch, and run this seat's own checks.
# Usage: run_partner.sh PATCH_FILE LABEL [profile]
set -euo pipefail
PATCH=$(realpath "$1")
LABEL="$2"
PROFILE="${3:-self}"
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
TREE="/tmp/partner-${LABEL}"
BUILD="/tmp/build-partner-${LABEL}"
OUT="$REPO/forge-combo29/grok/$S/partner_${LABEL}"
mkdir -p "$OUT"
rm -rf "$TREE" "$BUILD"
git -C "$REPO" worktree prune
git -C "$REPO" worktree add --detach "$TREE" "$BASE"
{
  echo "patch=$PATCH"
  if git -C "$TREE" apply --check "$PATCH"; then
    echo "apply_check=yes"
  else
    echo "apply_check=no"
    exit 1
  fi
  git -C "$TREE" apply "$PATCH"
  echo "apply=yes"
} | tee "$OUT/apply.txt"
cmake -S "$TREE/forge-combo29" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++
cmake --build "$BUILD" -j4
python3 "$REPO/forge-combo29/grok/$S/run_honesty.py" "$BUILD/forge" "partner_${LABEL}" "$OUT/HONESTY.txt"
python3 "$REPO/forge-combo29/grok/$S/harness_search.py" --exe "$BUILD/forge" \
  --fens /tmp/kimi5/forge-combo29/tests_kimi5_job3/first200.fens --depth 12 \
  --out "$OUT/off_O_d12" --switch false --profile "$PROFILE"
python3 "$REPO/forge-combo29/grok/$S/harness_search.py" --exe "$BUILD/forge" \
  --fens /tmp/kimi5/forge-combo29/tests_kimi5_job3/first200.fens --depth 12 \
  --out "$OUT/on_O_d12" --switch true --profile "$PROFILE"
python3 "$REPO/forge-combo29/grok/$S/compare_rows.py" \
  "$REPO/forge-combo29/grok/$S/B_O_d12.rows" "$OUT/off_O_d12.rows" > "$OUT/compare_off.txt"
python3 "$REPO/forge-combo29/grok/$S/compare_rows.py" \
  "$REPO/forge-combo29/grok/$S/B_O_d12.rows" "$OUT/on_O_d12.rows" > "$OUT/compare_on_vs_B.txt"
echo "partner_build_exe=$BUILD/forge" | tee "$OUT/build.txt"
