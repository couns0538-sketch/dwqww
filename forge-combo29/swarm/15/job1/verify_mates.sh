#!/usr/bin/env bash
# verify_mates.sh : runs solvemate2.py on every position of mates_d12.txt and prints
# idx | engine score | PV plies | true distance | verdict
set -u
cd "$(dirname "$0")"
while IFS='|' read -r idx fen sc plies mateq rest; do
  idx=$(echo "$idx" | tr -d ' ')
  case "$idx" in ''|idx) continue;; esac
  fen=$(echo "$fen")
  sc=$(echo "$sc" | sed 's/  */ /g')
  plies=$(echo "$plies" | tr -d ' ')
  truth=$(timeout 300 python3 solvemate2.py "$fen" 16 2>&1 | tail -1)
  printf "%s | engine %s | pv %s plies | %s\n" "$idx" "$sc" "$plies" "$truth"
done < mates_parsed.txt
