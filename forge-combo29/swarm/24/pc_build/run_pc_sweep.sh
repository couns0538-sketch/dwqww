#!/usr/bin/env bash
# seat 24, area 4: Threads sweep (2/4/8/16) on the PC r15 TSan build under PC20, first 100 of G, depth 12.
# NOTE ON SCORES: this job reports only event counts (TSan blocks, crashes, hangs, illegal bestmoves).
# The swarm rule says every SCORE must be Threads 1; a race test needs >1 thread, so no score is reported here.
set -u
cd "$(dirname "$0")"
EXE="$HOME/work/pcsrc/forge-combo29/build-pc-tsan/forge"
echo "$(date -u) start PC-build Threads sweep (PC20, first 100 of G)" >> stamps.txt
for T in 2 4 8 16; do
  echo "$(date -u) begin Threads $T" >> stamps.txt
  python3 pc_threads_sweep.py --exe "$EXE" --fens ../job1/set_G.epd --count 100 --threads "$T" \
      --depth 12 --out "pcT$T" >> "pcT$T.run.log" 2>&1
  echo "$(date -u) end Threads $T exit=$?" >> stamps.txt
done
echo "$(date -u) done PC-build Threads sweep" >> stamps.txt
