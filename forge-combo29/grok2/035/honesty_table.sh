#!/usr/bin/env bash
# honesty_table.sh: print the signature line of each honesty raw file
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
for f in "$D"/honesty_*.txt; do
  echo "== $(basename "$f")"
  if [[ "$(basename "$f")" == *perft* ]]; then
    tail -n 1 "$f"
  else
    grep 'bench depth' "$f"
  fi
done
