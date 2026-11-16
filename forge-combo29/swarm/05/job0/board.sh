#!/usr/bin/env bash
# board.sh : reads every seat's FINDINGS.md + newest STATUS block into /tmp/board/<seat>.md
set -u
cd /agent/repos/dwqww
mkdir -p /tmp/board
for s in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort); do
  git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$s" 2>/dev/null || continue
  {
    echo "########## seat $s ##########"
    echo "--- FINDINGS.md ---"
    git show "FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md" 2>/dev/null || echo "(none)"
    echo "--- STATUS.md tail ---"
    git show "FETCH_HEAD:forge-combo29/swarm/$s/STATUS.md" 2>/dev/null | tail -14 || echo "(none)"
  } > "/tmp/board/$s.md"
done
wc -l /tmp/board/*.md | tail -1
