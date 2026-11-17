#!/usr/bin/env bash
# Production sweep for the small families. Bounded per-search wall clock so a single
# runaway search cannot eat the run; every timeout is counted, not hidden.
set -u
EXE=${EXE:-/tmp/fx/build/forge}
OUT=${OUT:-/tmp/fx/prod}
ST=${SEARCH_TIMEOUT:-25}
W=${WORKERS:-4}
mkdir -p "$OUT"

echo "exe=$EXE st=$ST w=$W start=$(date -u +%H:%M:%SZ)" >> "$OUT/run.log"
for fam in KQK KRK KBNK KBK KNK; do
  for go in "go depth 12" "go nodes 12000"; do
    for arm in oracle engine; do
      tag="${fam}_${arm}_$(echo "$go" | tr ' ' '_')"
      [ -d "$OUT/$tag" ] && [ -f "$OUT/$tag/_run.json" ] && { echo "SKIP $tag" >> "$OUT/run.log"; continue; }
      python3 /tmp/fx/parallel.py --family "$fam" --go "$go" --arm "$arm" \
        --n 20 --workers "$W" --outdir "$OUT/$tag" --search-timeout "$ST" \
        >> "$OUT/run.log" 2>&1
      echo "DONE $tag $(date -u +%H:%M:%SZ)" >> "$OUT/run.log"
    done
  done
done
echo "ALL DONE $(date -u +%H:%M:%SZ)" >> "$OUT/run.log"
