#!/usr/bin/env bash
# Review the partner seat for idea 17. Harness is this script plus uci_suite.py.
# Never copies a partner script. Prints PARTNER <nnn|none>.
set -u
REPO=$(cat ~/grok_repo.txt)
SEAT=$(cat ~/grok_seat.txt)
DIR="$REPO/forge-combo29/grok/$SEAT"
cd "$REPO"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7

pick_partner() {
  local have67=0 have117=0
  git ls-remote --heads origin refs/heads/for-fable-and-opus/grok-067 | grep -q . && have67=1
  git ls-remote --heads origin refs/heads/for-fable-and-opus/grok-117 | grep -q . && have117=1
  if [ "$have67" = 1 ]; then echo 067; return; fi
  if [ "$have117" = 1 ]; then echo 117; return; fi
  echo none
}

PARTNER=$(pick_partner)
echo "PARTNER $PARTNER"
if [ "$PARTNER" = none ]; then
  exit 0
fi
git fetch -q --depth 1 "origin" "for-fable-and-opus/grok-$PARTNER:refs/remotes/origin/grok-$PARTNER"
if ! git cat-file -e "origin/grok-$PARTNER:forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
  echo "NO_PATCH $PARTNER"
  exit 2
fi
git show "origin/grok-$PARTNER:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$DIR/partner_$PARTNER.patch.txt"
echo "PATCH_BYTES $(wc -c < "$DIR/partner_$PARTNER.patch.txt")"
if git cat-file -e "origin/grok-$PARTNER:forge-combo29/grok/$PARTNER/RESULT.txt" 2>/dev/null; then
  git show "origin/grok-$PARTNER:forge-combo29/grok/$PARTNER/RESULT.txt" > "$DIR/partner_$PARTNER.RESULT.txt"
  echo "PARTNER_RESULT $(cat "$DIR/partner_$PARTNER.RESULT.txt")"
else
  echo "PARTNER_RESULT missing"
fi
rm -rf /tmp/partner-work
git worktree add --detach /tmp/partner-work "$BASE"
cd /tmp/partner-work
if git apply --check "$DIR/partner_$PARTNER.patch.txt"; then
  echo "APPLY_CHECK ok"
else
  echo "APPLY_CHECK fail"
  exit 3
fi
git apply "$DIR/partner_$PARTNER.patch.txt"
echo "APPLY ok"
cmake -S /tmp/partner-work/forge-combo29 -B /tmp/build-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ > /tmp/cmake-partner.log 2>&1
cmake --build /tmp/build-partner -j4 > /tmp/build-partner.log 2>&1
echo "BUILD ok $(ls -la /tmp/build-partner/forge)"
