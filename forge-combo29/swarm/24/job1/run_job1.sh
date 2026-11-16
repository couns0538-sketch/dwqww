#!/usr/bin/env bash
# seat 24, area 4, job 1: first 100 of G at depth 12, S14, Threads 2/4/8/16, under ThreadSanitizer.
# One fresh engine process per Threads setting (the driver starts and quits it), 100 positions each.
set -u
cd "$(dirname "$0")"
S=24
EXE=/agent/repos/base/forge-combo29/build-tsan/forge
echo "$(date -u) start job1 threads sweep" >> stamps.txt
for T in 2 4 8 16; do
  echo "$(date -u) begin Threads $T" >> stamps.txt
  python3 driver.py --exe "$EXE" --fens set_G.epd --count 100 --threads "$T" --depth 12 \
      --hash 16 --opts S14 --timeout 600 --out "t$T" >> "t$T.run.log" 2>&1
  echo "$(date -u) end Threads $T exit=$?" >> stamps.txt
done
echo "$(date -u) done job1" >> stamps.txt
