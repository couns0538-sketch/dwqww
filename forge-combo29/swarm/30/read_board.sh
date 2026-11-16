#!/usr/bin/env bash
# read the board: for each seat branch, show its FINDINGS.md lines
set -u
OUT=${1:-/tmp/board}
mkdir -p "$OUT"
git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*refs/heads/for-fable-and-opus/swarm-##' | sort > "$OUT/seats.txt"
for s in $(cat "$OUT/seats.txt"); do
  git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$s" 2>/dev/null || { echo "FETCHFAIL $s"; continue; }
  git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md > "$OUT/F$s.md" 2>/dev/null || echo "(no FINDINGS)" > "$OUT/F$s.md"
  git show FETCH_HEAD:forge-combo29/swarm/$s/STATUS.md > "$OUT/ST$s.md" 2>/dev/null || echo "(no STATUS)" > "$OUT/ST$s.md"
  git show FETCH_HEAD:forge-combo29/swarm/$s/HONESTY.txt > "$OUT/H$s.txt" 2>/dev/null
  echo "$s $(git rev-parse FETCH_HEAD | cut -c1-8) F=$(wc -l < "$OUT/F$s.md") S=$(wc -l < "$OUT/ST$s.md") H=$( [ -s "$OUT/H$s.txt" ] && echo y || echo n )"
done > "$OUT/index.txt"
cat "$OUT/index.txt"
