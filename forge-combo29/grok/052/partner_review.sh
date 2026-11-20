#!/usr/bin/env bash
# Review the partner seat with this seat's own harness. Does not copy their scripts.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
D="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7

pick_partner() {
  local has102=0 has002=0
  git ls-remote --heads origin "refs/heads/for-fable-and-opus/grok-102" | grep -q . && has102=1
  git ls-remote --heads origin "refs/heads/for-fable-and-opus/grok-002" | grep -q . && has002=1
  if [ "$has102" = 1 ]; then echo 102; return; fi
  if [ "$has002" = 1 ]; then echo 002; return; fi
  echo none
}

P=$(pick_partner)
echo "PARTNER $P"
echo "$P" > "$D/partner_seat.txt"
if [ "$P" = none ]; then
  echo "NO_PARTNER"
  exit 0
fi

git fetch -q --depth 1 origin "for-fable-and-opus/grok-$P" || { echo FAIL_FETCH; exit 2; }
if ! git cat-file -e "FETCH_HEAD:forge-combo29/grok/$P/idea.patch.txt" 2>/dev/null; then
  echo "NO_PATCH_YET"
  exit 3
fi
git show "FETCH_HEAD:forge-combo29/grok/$P/idea.patch.txt" > "$D/partner.patch.txt"
echo "PATCH_BYTES $(wc -c < "$D/partner.patch.txt")"

WT=/tmp/partner-base
rm -rf "$WT"
git worktree add "$WT" "$BASE"
cd "$WT"
if ! git apply --check "$D/partner.patch.txt"; then
  echo "APPLY_CHECK_FAIL"
  exit 4
fi
echo "APPLY_CHECK_OK"
git apply "$D/partner.patch.txt"
cmake -S forge-combo29 -B /tmp/partner-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/partner-build -j3
echo "PARTNER_BUILD_OK"
