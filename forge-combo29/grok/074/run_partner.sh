#!/usr/bin/env bash
# Review seat 024 (same idea) with this seat's own harness. Not a copy of theirs.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
SEAT_DIR="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
cd "$REPO"
git fetch -q --depth 1 origin for-fable-and-opus/grok-024 || { echo "FAIL fetch partner"; exit 2; }
echo "PARTNER_HEAD $(git rev-parse FETCH_HEAD)"
git ls-tree -r --name-only FETCH_HEAD | grep 'forge-combo29/grok/024/' | tee "$SEAT_DIR/partner_files.txt"
if ! git cat-file -e "FETCH_HEAD:forge-combo29/grok/024/idea.patch.txt" 2>/dev/null; then
  echo "NO_PATCH"
  exit 3
fi
git show "FETCH_HEAD:forge-combo29/grok/024/idea.patch.txt" > "$SEAT_DIR/partner.patch.txt"
echo "PATCH_BYTES $(wc -c < "$SEAT_DIR/partner.patch.txt")"
WT=/agent/repos/partner-024
if [ ! -d "$WT" ]; then
  git worktree add "$WT" "$BASE"
fi
cd "$WT"
git checkout -q -- . || true
git apply --check "$SEAT_DIR/partner.patch.txt"
echo "APPLY_CHECK_OK"
git apply "$SEAT_DIR/partner.patch.txt"
echo "APPLY_OK"
cmake -S "$WT/forge-combo29" -B "$WT/forge-combo29/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$WT/forge-combo29/build" -j 4
echo "BUILD_OK"
