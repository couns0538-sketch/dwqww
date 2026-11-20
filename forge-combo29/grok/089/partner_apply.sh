#!/usr/bin/env bash
# Apply a partner patch onto a fresh base worktree and release-build it.
# Usage: partner_apply.sh PATCH_FILE WORKTREE_DIR
set -u
PATCH="$1"
WT="$2"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
git worktree add "$WT" "$BASE"
cd "$WT"
git apply --check "$PATCH"
echo APPLY_CHECK_OK
git apply "$PATCH"
echo APPLY_OK
cmake -S forge-combo29 -B forge-combo29/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build forge-combo29/build -j4
echo BUILD_OK "$WT/forge-combo29/build/forge"
