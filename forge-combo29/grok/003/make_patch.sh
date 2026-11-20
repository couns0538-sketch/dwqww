#!/usr/bin/env bash
# Export the work-tree diff and check that it applies to the plain base.
set -u
SEAT=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
PATCH="$REPO/forge-combo29/grok/$SEAT/idea.patch.txt"
cd /agent/repos/work
git diff -- forge-combo29/include/forge/search.hpp forge-combo29/src/search.cpp forge-combo29/src/uci.cpp > "$PATCH"
cd /agent/repos/base
git apply --check "$PATCH"
echo "APPLY_CHECK_OK $PATCH"
wc -l "$PATCH"
