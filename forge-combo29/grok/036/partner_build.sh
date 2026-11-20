#!/usr/bin/env bash
# Fresh base worktree, apply the partner patch, release-build with g++.
# Prints PARTNER_PATCH_MISSING if idea.patch.txt is not on the branch yet.
set -u
PARTNER="${1:?partner seat}"
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER" || { echo "FAIL fetch partner"; exit 2; }
if ! git cat-file -e FETCH_HEAD:"forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
  echo "PARTNER_PATCH_MISSING"
  git ls-tree -r --name-only FETCH_HEAD | grep "forge-combo29/grok/$PARTNER/" || true
  exit 10
fi
WT="/agent/repos/partner-$PARTNER"
rm -rf "$WT"
git worktree add --detach "$WT" 6b98f2170a3210e71beed04bbd2553972c253ed7
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$REPO/forge-combo29/grok/$S/partner_idea.patch.txt"
cd "$WT"
if git apply --check "$REPO/forge-combo29/grok/$S/partner_idea.patch.txt"; then
  echo "partner git apply --check: ok" | tee "$REPO/forge-combo29/grok/$S/partner_apply_check.txt"
else
  echo "partner git apply --check: FAIL" | tee "$REPO/forge-combo29/grok/$S/partner_apply_check.txt"
  exit 3
fi
git apply "$REPO/forge-combo29/grok/$S/partner_idea.patch.txt"
cmake -S "$WT/forge-combo29" -B "$WT/forge-combo29/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$WT/forge-combo29/build" -j 4
echo "PARTNER_BUILT $WT/forge-combo29/build/forge"
