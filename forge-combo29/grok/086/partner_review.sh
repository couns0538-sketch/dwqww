#!/usr/bin/env bash
# Review the partner patch on a fresh base worktree. Written before the review runs.
# Usage: partner_review.sh PARTNER_SEAT
set -u
PARTNER="$1"
REPO="$(cat ~/grok_repo.txt)"
S="$(cat ~/grok_seat.txt)"
MINE="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
WT="/tmp/partner-$PARTNER"
rm -rf "$WT"
git -C "$REPO" worktree add "$WT" "$BASE"
cd "$WT"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$MINE/partner_idea.patch.txt"
echo "fetched partner $PARTNER patch bytes $(wc -c < "$MINE/partner_idea.patch.txt")"
git apply --check "$MINE/partner_idea.patch.txt"
echo "partner_apply_check_exit=$?"
git apply "$MINE/partner_idea.patch.txt"
echo "partner_apply_exit=$?"
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build build -j4
echo "partner_build_exit=$?"
echo "$WT/forge-combo29/build/forge" > "$MINE/partner_exe.txt"
