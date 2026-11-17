#!/bin/sh
# pins.sh EXE OUTFILE — the 11 documented lock pins (LOCK.md), Threads 1, Hash 16,
# OwnBook false. Net on: bench 11/13/16/20/22. Net off: the same five. Plus perft 5.
set -e
exe="$1"; out="$2"
{
  printf 'uci\nisready\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
  printf 'setoption name OwnBook value false\nsetoption name UseNNUE value true\n'
  for d in 11 13 16 20 22; do printf 'bench %s\n' "$d"; done
  printf 'setoption name UseNNUE value false\n'
  for d in 11 13 16 20 22; do printf 'bench %s\n' "$d"; done
  printf 'position startpos\ngo perft 5\nquit\n'
} | "$exe" 2>&1 | grep -E 'bench depth|^nodes' > "$out"
cat "$out"
