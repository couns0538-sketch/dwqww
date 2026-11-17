#!/usr/bin/env bash
# confirms.sh PATTERN : does any seat already have a C line about PATTERN?
set -u
cd "$(git rev-parse --show-toplevel)"
for s in $(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort); do
  git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$s" 2>/dev/null || continue
  git show "FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md" 2>/dev/null | grep -i -- "$1" | sed "s#^#seat $s: #"
done
