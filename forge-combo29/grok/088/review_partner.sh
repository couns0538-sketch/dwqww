#!/usr/bin/env bash
# Review a partner patch on a fresh base worktree.
# usage: review_partner.sh PATCH OPTION OUTDIR
# OPTION is the check name (IdeaA7). Builds /tmp/forge-partner.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
PATCH=$1
OPTION=$2
TAG=$3
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
WT=/tmp/partner-work
BUILD=/tmp/forge-partner
rm -rf "$WT" "$BUILD"
git -C "$REPO" worktree add "$WT" "$BASE"
cd "$WT"
if ! git apply --check "$PATCH"; then
  echo "APPLY_CHECK_FAIL"
  exit 2
fi
echo "APPLY_CHECK_OK"
git apply "$PATCH"
cmake -S "$WT/forge-combo29" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$BUILD" -j 4
echo "BUILD_OK $BUILD/forge"
echo "$TAG" > /tmp/partner_tag.txt
