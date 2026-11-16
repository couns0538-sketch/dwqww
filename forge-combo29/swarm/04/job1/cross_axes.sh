#!/usr/bin/env bash
# cross_axes.sh — area 4 hang investigation, part 2: which axis drives the node explosion?
# Same FEN 5R2/1p5k/6p1/8/1K6/5q2/8/8 throughout. Fresh process per run, stdout read to
# bestmove before anything else is written (hang_repro.py does that).
set -u
D=/agent/repos/dwqww/forge-combo29/swarm/04/job1
EXE=/home/ubuntu/builds/rel/forge
OUT=/home/ubuntu/runs/hang
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) begin cross axes" >> $OUT/stamps.txt
for t in 2 3 5 8; do
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) threads $t depth 12" >> $OUT/stamps.txt
  python3 $D/hang_repro.py $EXE $OUT "t${t}_d12" --runs 8 --threads $t --depth 12 --limit 120 \
    >> $OUT/cross.log 2>&1
done
for dep in 10 11 13; do
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) threads 4 depth $dep" >> $OUT/stamps.txt
  python3 $D/hang_repro.py $EXE $OUT "t4_d${dep}" --runs 8 --threads 4 --depth $dep --limit 120 \
    >> $OUT/cross.log 2>&1
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) begin unlimited-depth runs" >> $OUT/stamps.txt
for t in 1 4; do
  python3 $D/hang_repro.py $EXE $OUT "t${t}_dinf" --runs 4 --threads $t --depth 13 --limit 180 \
    >> $OUT/cross.log 2>&1
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) cross axes DONE" >> $OUT/stamps.txt
