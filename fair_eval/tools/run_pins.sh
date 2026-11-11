#!/usr/bin/env bash
# run_pins.sh <exe> <out file> [extra "setoption ..." lines]  - JOB D (own code, 2026-11-11)
# One process: Threads 1, Hash 16, OwnBook false; bench 11/13/16/20/22 net on, the same net off, perft 5.
# `bench` builds a fresh Searcher(16) per call (uci.cpp), so the order of the benches does not change node counts.
set -u
exe="$1"; out="$2"; shift 2
{
  echo uci
  echo "setoption name Threads value 1"; echo "setoption name Hash value 16"; echo "setoption name OwnBook value false"
  for o in "$@"; do echo "$o"; done
  echo isready
  for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "setoption name UseNNUE value false"
  for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "go perft 5"
  echo quit
} | "$exe" > "$out" 2>&1
echo "exit $? $(md5sum "$exe" | cut -c1-32)" >> "$out"
grep -a -E "bench depth|perft|Nodes|nodes searched|^exit" "$out" | cut -c1-120
