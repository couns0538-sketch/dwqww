#!/usr/bin/env bash
# Evaluate seat 093's IdeaK4 patch with this seat's harness. Not their scripts.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
mkdir -p /tmp/partner093 "forge-combo29/grok/$S/partner"
git fetch -q --depth 1 origin for-fable-and-opus/grok-093 || { echo "FAIL fetch partner"; exit 2; }
echo "partner_head $(git rev-parse FETCH_HEAD)" | tee "forge-combo29/grok/$S/partner/fetch.txt"
if ! git cat-file -e FETCH_HEAD:forge-combo29/grok/093/idea.patch.txt; then
  echo "NO_PATCH" | tee "forge-combo29/grok/$S/partner/fetch.txt"
  exit 3
fi
git show FETCH_HEAD:forge-combo29/grok/093/idea.patch.txt > "forge-combo29/grok/$S/partner/their.patch.txt"
git show FETCH_HEAD:forge-combo29/grok/093/O_P_on.rows.txt > "forge-combo29/grok/$S/partner/their_O_on.rows.txt"
git show FETCH_HEAD:forge-combo29/grok/093/proof_on_O.txt > "forge-combo29/grok/$S/partner/their_proof_on_O.txt"
git show FETCH_HEAD:forge-combo29/grok/093/proof_off_O.txt > "forge-combo29/grok/$S/partner/their_proof_off_O.txt"
WT=/agent/repos/partner093
if [ -d "$WT" ]; then
  git worktree remove --force "$WT" || rm -rf "$WT"
fi
git worktree add "$WT" "$BASE"
cd "$WT"
git apply --check "$REPO/forge-combo29/grok/$S/partner/their.patch.txt"
echo APPLY_CHECK_OK | tee "$REPO/forge-combo29/grok/$S/partner/apply_check.txt"
git apply "$REPO/forge-combo29/grok/$S/partner/their.patch.txt"
mkdir -p "$WT/forge-combo29/build"
cmake -S "$WT/forge-combo29" -B "$WT/forge-combo29/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$WT/forge-combo29/build" -j4
EXE="$WT/forge-combo29/build/forge"
python3 "$REPO/forge-combo29/grok/$S/scripts/honesty_run.py" "$EXE" "$REPO/forge-combo29/grok/$S/partner/honesty"
python3 "$REPO/forge-combo29/grok/$S/scripts/search_set.py" "$EXE" "$REPO/forge-combo29/grok/$S/positions/first200.fens" 12 "$REPO/forge-combo29/grok/$S/partner/off_O.txt" "setoption name IdeaK4 value false"
python3 "$REPO/forge-combo29/grok/$S/scripts/search_set.py" "$EXE" "$REPO/forge-combo29/grok/$S/positions/first200.fens" 12 "$REPO/forge-combo29/grok/$S/partner/on_O.txt" "setoption name IdeaK4 value true,setoption name IdeaK4_Shrink value 24"
python3 "$REPO/forge-combo29/grok/$S/scripts/compare_nodes.py" "$REPO/forge-combo29/grok/$S/partner/off_O.txt" "$REPO/forge-combo29/grok/$S/honesty/B_O_d12.txt" | tee "$REPO/forge-combo29/grok/$S/partner/cmp_off_O.txt"
python3 "$REPO/forge-combo29/grok/$S/scripts/compare_partner_rows.py" "$REPO/forge-combo29/grok/$S/partner/on_O.txt" "$REPO/forge-combo29/grok/$S/partner/their_O_on.rows.txt" | tee "$REPO/forge-combo29/grok/$S/partner/cmp_on_O.txt"
echo PARTNER_SEARCH_DONE
