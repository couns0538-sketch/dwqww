#!/usr/bin/env bash
# Review one partner seat. Fetch, copy their patch, apply on a fresh base, build.
# Measurements are separate calls of this seat's own harnesses.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
PARTNER="$1"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
DEST="forge-combo29/grok/$S"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER" || { echo "FAIL fetch $PARTNER"; exit 2; }
echo "FETCH_HEAD $(git rev-parse FETCH_HEAD)" | tee "$DEST/partner_${PARTNER}_fetch.txt"
git ls-tree -r --name-only FETCH_HEAD "forge-combo29/grok/$PARTNER" | tee "$DEST/partner_${PARTNER}_ls.txt"
if ! git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
  echo "NO_PATCH"
  exit 3
fi
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$DEST/partner_${PARTNER}_idea.patch.txt"
echo "PATCH_BYTES $(wc -c < "$DEST/partner_${PARTNER}_idea.patch.txt")"
WT="/agent/repos/partner-$PARTNER"
if [ ! -d "$WT" ]; then
  git worktree add --detach "$WT" "$BASE"
fi
cd "$WT"
git apply --check "$(cat ~/grok_repo.txt)/$DEST/partner_${PARTNER}_idea.patch.txt"
echo "APPLY_CHECK ok"
git checkout -- . >/dev/null 2>&1 || true
git apply "$(cat ~/grok_repo.txt)/$DEST/partner_${PARTNER}_idea.patch.txt"
echo "APPLY ok"
cd "$WT/forge-combo29"
if [ ! -f build-rel/forge ]; then
  cmake -S . -B build-rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
fi
cmake --build build-rel -j4
echo "EXE $WT/forge-combo29/build-rel/forge"
