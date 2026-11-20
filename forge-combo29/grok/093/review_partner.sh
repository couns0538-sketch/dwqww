#!/usr/bin/env bash
# Review one partner patch on a fresh base worktree. Not a copy of their harness.
# Usage: review_partner.sh PATCH_FILE PARTNER_O_RAW
# PARTNER_O_RAW may be the word none.
set -eu
PATCH=$(readlink -f "$1")
PARTNER_O=${2:-none}
if [ "$PARTNER_O" != "none" ]; then PARTNER_O=$(readlink -f "$PARTNER_O"); fi
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
TREE=/agent/repos/partner
git -C "$REPO" worktree remove --force "$TREE" 2>/dev/null || true
rm -rf "$TREE"
git -C "$REPO" worktree add "$TREE" 6b98f2170a3210e71beed04bbd2553972c253ed7
cd "$TREE"
git apply --check "$PATCH"
echo APPLY_CHECK_OK
git apply "$PATCH"
echo APPLY_OK
git diff --stat
cmake -S "$TREE/forge-combo29" -B "$TREE/forge-combo29/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$TREE/forge-combo29/build" -j 4
EXE="$TREE/forge-combo29/build/forge"
python3 "$DIR/honesty_run.py" "$EXE" HONESTY_PARTNER
python3 "$DIR/search_set.py" "$EXE" /tmp/grok093_sets/first200.fens 12 "$DIR/O_partner_off"
python3 "$DIR/compare_raw.py" "$DIR/O_B_d12.raw.txt" "$DIR/O_partner_off.raw.txt" | tee "$DIR/proof_partner_off.txt"
python3 "$DIR/search_set.py" "$EXE" /tmp/grok093_sets/first200.fens 12 "$DIR/O_partner_on" IdeaK4=true
if [ "$PARTNER_O" != "none" ] && [ -f "$PARTNER_O" ]; then
  python3 "$DIR/compare_raw.py" "$PARTNER_O" "$DIR/O_partner_on.raw.txt" | tee "$DIR/proof_partner_on.txt"
else
  python3 "$DIR/sum_nodes.py" "$DIR/O_partner_on.raw.txt" | tee "$DIR/proof_partner_on.txt"
  echo "partner_O_raw=none" | tee -a "$DIR/proof_partner_on.txt"
fi
python3 "$DIR/compare_raw.py" "$DIR/O_B_d12.raw.txt" "$DIR/O_partner_on.raw.txt" | tee "$DIR/proof_partner_on_vs_B.txt"
echo PARTNER_SEARCH_DONE
