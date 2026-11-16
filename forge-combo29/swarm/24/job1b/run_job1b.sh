#!/usr/bin/env bash
# seat 24, area 4, job 1 REPEAT: first 100 of the R set (seed 2411) at depth 12, S14, Threads 2 and 4, under TSan.
# Then the planted-fault control through the SAME runner.
set -u
cd "$(dirname "$0")"
EXE=/agent/repos/base/forge-combo29/build-tsan/forge
PLANTED="$HOME/work/planted/build-tsan/forge"
echo "$(date -u) start job1b repeat (R seed 2411, first 100)" >> stamps.txt
for T in 2 4; do
  echo "$(date -u) begin Threads $T" >> stamps.txt
  python3 driver.py --exe "$EXE" --fens r_positions_2411.fens --count 100 --threads "$T" --depth 12 \
      --hash 16 --opts S14 --timeout 600 --out "r$T" >> "r$T.run.log" 2>&1
  echo "$(date -u) end Threads $T exit=$?" >> stamps.txt
done
echo "$(date -u) start job1b planted control" >> stamps.txt
python3 driver.py --exe "$PLANTED" --fens r_positions_2411.fens --count 6 --threads 4 --depth 12 \
    --hash 16 --opts S14 --timeout 600 --out planted_b >> planted_b.run.log 2>&1
echo "$(date -u) end job1b planted control exit=$?" >> stamps.txt
echo -n "planted_b TSan blocks: "; grep -c "WARNING: ThreadSanitizer" planted_b.raw
echo "$(date -u) done job1b" >> stamps.txt
