#!/usr/bin/env bash
# board.sh : fetch every seat's FINDINGS.md (and last STATUS block) into ./board/
set -u
cd /agent/repos/dwqww
mkdir -p board
for n in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##'); do
  [ -s "board/$n.FINDINGS.md" ] && continue
  if git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$n" 2>/dev/null; then
    git show "FETCH_HEAD:forge-combo29/swarm/$n/FINDINGS.md" > "board/$n.FINDINGS.md" 2>/dev/null || : > "board/$n.FINDINGS.md"
    git show "FETCH_HEAD:forge-combo29/swarm/$n/STATUS.md" > "board/$n.STATUS.md" 2>/dev/null || : > "board/$n.STATUS.md"
  fi
done
wc -l board/*.FINDINGS.md | tail -1
