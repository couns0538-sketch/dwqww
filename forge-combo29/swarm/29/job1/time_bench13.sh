#!/usr/bin/env bash
# wall time of one fresh-process `bench 13` (P1), 5 runs. Timing by bash's own EPOCHREALTIME (monotonic enough
# at second+nanosecond resolution for a ~1 s run) and by the engine's own nodes/second line as a cross-check.
set -u
EXE="$1"
for i in 1 2 3 4 5; do
  t0=$EPOCHREALTIME
  printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' > /tmp/bin_$i.txt
  out=$("$EXE" < /tmp/bin_$i.txt 2>&1 | grep -oE "nodes [0-9]+ nps [0-9]+|Nodes: [0-9]+|nps[ =:]+[0-9]+" | tail -2 | tr '\n' ' ')
  t1=$EPOCHREALTIME
  awk -v a="$t0" -v b="$t1" -v i="$i" -v o="$out" 'BEGIN{printf "run%d real %.3f s   engine: %s\n", i, b-a, o}'
done
