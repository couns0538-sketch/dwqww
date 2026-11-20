#!/usr/bin/env bash
# Review one partner patch on a fresh base. Harness is this seat's, not the partner's.
# usage: review_partner.sh PATCH_FILE OPTION_ON
# OPTION_ON is one setoption line, for example: setoption name IdeaS27 value true
set -eu
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
PATCH=$1
ON_LINE=$2
OFF_LINE=${ON_LINE/ value true/ value false}
DIR="forge-combo29/grok/$S"
TAG=$(basename "$(dirname "$PATCH")")
# dirname of a fetched copy may not be the seat. The caller passes TAG via the patch path's parent.
if [ -n "${3:-}" ]; then TAG=$3; fi
PREFIX="$DIR/partner_${TAG}"
mkdir -p "$PREFIX"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
if [ ! -d /tmp/partner-base/forge-combo29 ]; then
  git worktree add /tmp/partner-base "$BASE"
fi
cd /tmp/partner-base
git checkout -q -- . || true
git apply --check "$PATCH"
echo "apply_check_exit $?" | tee "$REPO/$PREFIX/apply_check.txt"
git apply "$PATCH"
echo "apply_exit $?" | tee -a "$REPO/$PREFIX/apply_check.txt"
cmake -S /tmp/partner-base/forge-combo29 -B /tmp/forge-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/forge-partner -j 3
cd "$REPO"
python3 "$DIR/honesty_check.py" /tmp/forge-partner/forge "honesty_${TAG}"
# honesty_check writes next to itself, under the seat folder, using the prefix.
python3 "$DIR/search_positions.py" /tmp/forge-partner/forge /tmp/O.fens 12 "$PREFIX/o_off_d12.txt" "$OFF_LINE"
python3 "$DIR/search_positions.py" /tmp/forge-partner/forge /tmp/O.fens 12 "$PREFIX/o_on_d12.txt" "$ON_LINE"
python3 "$DIR/parse_nodes.py" "$PREFIX/o_off_d12.txt" "$PREFIX/o_off_d12.nodes"
python3 "$DIR/parse_nodes.py" "$PREFIX/o_on_d12.txt" "$PREFIX/o_on_d12.nodes"
echo "OFF_VS_B" | tee "$PREFIX/compare.txt"
python3 "$DIR/compare_nodes.py" "$DIR/o_b_d12.nodes" "$PREFIX/o_off_d12.nodes" | tee -a "$PREFIX/compare.txt"
echo "PARTNER_REVIEW_SEARCH_OK"
