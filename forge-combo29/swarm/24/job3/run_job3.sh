#!/usr/bin/env bash
# seat 24, area 4, job 3: `go infinite` + stop after 1..200 ms at Threads 8, 1000 times, under ThreadSanitizer.
# Then the same loop through the planted-fault executable, which must be counted (that is the proof).
set -u
cd "$(dirname "$0")"
EXE=/agent/repos/base/forge-combo29/build-tsan/forge
PLANTED="$HOME/work/planted/build-tsan/forge"
echo "$(date -u) start job3 infinite/stop 1000" >> stamps.txt
python3 infinite_stop.py --exe "$EXE" --fens ../job1/set_G.epd --rounds 1000 --threads 8 --hash 16 \
    --seed 2403 --out inf8 > inf8.run.log 2>&1
echo "$(date -u) end job3 real run exit=$?" >> stamps.txt
if [ -x "$PLANTED" ]; then
  echo "$(date -u) start job3 planted control" >> stamps.txt
  python3 infinite_stop.py --exe "$PLANTED" --fens ../job1/set_G.epd --rounds 8 --threads 8 --hash 16 \
      --seed 2404 --out planted3 > planted3.run.log 2>&1
  echo "$(date -u) end job3 planted control exit=$?" >> stamps.txt
  echo -n "planted3 TSan report blocks: "; grep -c "WARNING: ThreadSanitizer" planted3.raw
else
  echo "$(date -u) PLANTED EXE MISSING at $PLANTED" >> stamps.txt
fi
echo "$(date -u) done job3" >> stamps.txt
