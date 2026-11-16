#!/usr/bin/env bash
# Quantifies how much of a reported `bench N` time is one-time table work that does not depend on depth.
# uci.cpp:610 takes the timer BEFORE `forge::Searcher bench_searcher(16)`, and the bench loop calls
# bench_searcher.clear() for each of the 8 positions, so the 16 MB transposition table is allocated once and
# zeroed 8 more times inside the measured window. callgrind counts that memset as a CONSTANT 227,022,192
# instructions in bench 1, 11 and 13 alike.
# This script measures the whole `bench D` and the engine's own reported `time`, for D = 1 and 13, and prints the
# difference between two runs of the SAME command first (the job asks for that: "the base at movetime 50 twice
# first" is area 8's wording; the equivalent here is the same bench twice).
set -u
EXE="$1"
for rep in 1 2; do
  for d in 1 13; do
    printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench %s\nquit\n' "$d" > /tmp/bt.txt
    t0=$EPOCHREALTIME
    out=$("$EXE" < /tmp/bt.txt)
    t1=$EPOCHREALTIME
    eng=$(echo "$out" | grep "bench depth" | grep -oE "time [0-9]+" | awk '{print $2}')
    awk -v a="$t0" -v b="$t1" -v e="$eng" -v d="$d" -v r="$rep" \
      'BEGIN{printf "rep%d bench %-2s  engine_time_ms %s  wall_ms %.1f\n", r, d, e, (b-a)*1000}'
  done
done
