#!/usr/bin/env bash
# run_all.sh — area 4 job 1: Threads 1,2,4,8,16 on the first 100 of G at depth 12, S14, two runs each.
# One fresh engine process per search (run_searches.py). Times come from `date -u` stamps in stamps.txt.
set -u
RUNNER=/agent/repos/dwqww/forge-combo29/swarm/04/job1/run_searches.py
EXE=/home/ubuntu/builds/tsan/forge
OUT=/home/ubuntu/runs
POS=/home/ubuntu/sets/G.epd
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start job1 runs" >> "$OUT/stamps.txt"
for rep in 1 2; do
  for t in 1 2 4 8 16; do
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) begin rep$rep threads$t" >> "$OUT/stamps.txt"
    python3 "$RUNNER" --exe "$EXE" --positions "$POS" --from 0 --count 100 \
      --depth 12 --threads "$t" --hash 16 --outdir "$OUT" --tag "rep${rep}_t${t}" \
      --timeout 300 > "$OUT/rep${rep}_t${t}.log" 2>&1
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) end rep$rep threads$t rc=$?" >> "$OUT/stamps.txt"
  done
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALL DONE" >> "$OUT/stamps.txt"
