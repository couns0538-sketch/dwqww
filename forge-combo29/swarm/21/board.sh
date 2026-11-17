#!/usr/bin/env bash
# board.sh : read the board — other seats' FINDINGS.md and newest STATUS block.
# For every swarm branch present on origin: fetch --depth 1, show FINDINGS.md lines
# that are finding or check rows, and the last STATUS block's date line.
set -u
cd "$(git rev-parse --show-toplevel)"
for s in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort); do
  git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$s" 2>/dev/null || { echo "seat $s FETCH FAIL"; continue; }
  f=$(git show "FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md" 2>/dev/null)
  st=$(git show "FETCH_HEAD:forge-combo29/swarm/$s/STATUS.md" 2>/dev/null | grep '^## ' | tail -1)
  n=$(printf '%s\n' "$f" | grep -c '^| [0-9]*-[FC][0-9]')
  echo "== seat $s  findings/checks: $n  newest status: ${st:-none}"
  printf '%s\n' "$f" | grep '^| [0-9]*-F[0-9]' | tail -3
done
