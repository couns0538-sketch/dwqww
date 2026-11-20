#!/usr/bin/env bash
# Review the next seat with idea 30. Wait up to 10 minutes for idea.patch.txt.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
D="$REPO/forge-combo29/grok/$S"
PARTNER=080
cd "$REPO"
found=""
for try in 1 2 3 4 5 6; do
  git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER" || { echo "FAIL fetch partner"; exit 2; }
  echo "try $try $(date -u +%Y-%m-%dT%H:%M:%SZ) $(git rev-parse FETCH_HEAD)" | tee -a "$D/partner_fetch.log"
  if git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
    found=yes
    break
  fi
  if [ "$try" -eq 6 ]; then
    break
  fi
  sleep 100
done
git ls-tree -r --name-only FETCH_HEAD "forge-combo29/grok/$PARTNER" > "$D/partner_files.txt"
if [ -z "$found" ]; then
  echo "NO_PATCH" | tee "$D/partner_status.txt"
  exit 0
fi
echo "HAS_PATCH $(git rev-parse FETCH_HEAD)" | tee "$D/partner_status.txt"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$D/partner_idea.patch.txt"
mkdir -p /tmp/partner-src
if [ ! -d /tmp/partner-src/forge-combo29 ]; then
  git worktree add --detach /tmp/partner-src 6b98f2170a3210e71beed04bbd2553972c253ed7
fi
cd /tmp/partner-src
git checkout -- . >/dev/null 2>&1 || true
git apply --check "$D/partner_idea.patch.txt" > "$D/partner_apply_check.txt" 2>&1
echo "apply_check_exit=$?" | tee -a "$D/partner_apply_check.txt"
if ! git apply "$D/partner_idea.patch.txt" > "$D/partner_apply.txt" 2>&1; then
  echo "APPLY_FAIL" | tee -a "$D/partner_status.txt"
  exit 0
fi
echo "APPLY_OK" | tee -a "$D/partner_status.txt"
rm -rf /tmp/forge-partner
CXX=g++ CC=gcc cmake -S /tmp/partner-src/forge-combo29 -B /tmp/forge-partner -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/forge-partner -j 4
echo "BUILD_EXIT=$?" | tee -a "$D/partner_status.txt"
