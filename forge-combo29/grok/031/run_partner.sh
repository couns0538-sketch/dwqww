#!/usr/bin/env bash
# Review one partner patch on a fresh base worktree. This script is ours.
# Usage: run_partner.sh PATCH_FILE PARTNER_SEAT
set -u
PATCH=$1
PARTNER=$2
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
D="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
WT=/tmp/partner-$PARTNER
rm -rf "$WT" /tmp/partner-build-$PARTNER
git -C "$REPO" worktree add "$WT" "$BASE"
cd "$WT"
if ! git apply --check "$PATCH"; then
  echo "APPLY_CHECK_FAIL"
  exit 2
fi
echo "APPLY_CHECK_OK"
git apply "$PATCH"
cmake -S forge-combo29 -B /tmp/partner-build-$PARTNER -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/partner-build-$PARTNER -j4
EXE=/tmp/partner-build-$PARTNER/forge
python3 "$D/honesty.py" "$EXE" "$D" "partner${PARTNER}"
python3 "$D/measure_set.py" "$EXE" "$D/first200.fens" "$D/partner${PARTNER}_off_O_d12" 12 "$D/opt_off.txt"
python3 "$D/measure_set.py" "$EXE" "$D/first200.fens" "$D/partner${PARTNER}_on_O_d12" 12 "$D/opt_on.txt"
python3 "$D/read_nodes.py" "$D/partner${PARTNER}_off_O_d12.txt" > "$D/partner${PARTNER}_off_O_d12.nodes.txt"
python3 "$D/read_nodes.py" "$D/partner${PARTNER}_on_O_d12.txt" > "$D/partner${PARTNER}_on_O_d12.nodes.txt"
echo "=== off versus our exe B ==="
python3 "$D/compare_nodes.py" "$D/B_O_d12.nodes.txt" "$D/partner${PARTNER}_off_O_d12.nodes.txt" > "$D/partner${PARTNER}_off_vs_B.txt"
tail -n 5 "$D/partner${PARTNER}_off_vs_B.txt"
echo "PARTNER_BUILD_DONE $PARTNER"
