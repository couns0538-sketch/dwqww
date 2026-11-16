#!/usr/bin/env bash
# board.sh : read the other seats' FINDINGS.md + newest STATUS block (area 3 seats + one seed-chosen seat)
set -u
OUT=board
mkdir -p "$OUT"
for seat in 03 13 23 33 43 53 07; do
  { echo "### seat $seat"
    if git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$seat" 2>/dev/null; then
      echo "--- FINDINGS.md"
      git show "FETCH_HEAD:forge-combo29/swarm/$seat/FINDINGS.md" 2>/dev/null || echo "(no FINDINGS.md)"
      echo "--- newest STATUS block"
      git show "FETCH_HEAD:forge-combo29/swarm/$seat/STATUS.md" 2>/dev/null | tail -40 || echo "(no STATUS.md)"
      echo "--- files at top level"
      git ls-tree --name-only "FETCH_HEAD:forge-combo29/swarm/$seat" 2>/dev/null
    else
      echo "(branch not fetchable)"
    fi
  } > "$OUT/seat_$seat.txt"
done
date -u
wc -l "$OUT"/*.txt
