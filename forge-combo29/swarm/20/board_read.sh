#!/usr/bin/env bash
# Read other seats' FINDINGS.md + newest STATUS block without touching my branch.
set -u
for s in "$@"; do
  br="for-fable-and-opus/swarm-$s"
  if git fetch -q --depth 1 origin "$br" 2>/dev/null; then
    echo "########## SEAT $s  ($br  $(git rev-parse --short FETCH_HEAD))"
    git show "FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md" 2>/dev/null || echo "(no FINDINGS.md)"
    echo "---------- STATUS tail"
    git show "FETCH_HEAD:forge-combo29/swarm/$s/STATUS.md" 2>/dev/null | tail -18 || echo "(no STATUS.md)"
    echo
  else
    echo "########## SEAT $s : fetch failed"
  fi
done
