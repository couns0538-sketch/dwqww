#!/usr/bin/env bash
# honesty check: fresh process per line, raw outputs saved
set -u
EXE="$1"
D="$(dirname "$0")"
cd "$D"
for b in 11 13 16; do
  printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench %s\nquit\n' "$b" \
    | "$EXE" > "raw_bench_$b.txt" 2>&1
  echo "bench $b -> $(grep -oE 'nodes [0-9]+' "raw_bench_$b.txt" | tail -1)"
done
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | "$EXE" > raw_perft5.txt 2>&1
echo "perft 5 -> $(grep -oE 'nodes [0-9]+' raw_perft5.txt | tail -1)"
sha256sum "$EXE"
"$EXE" <<< "uci
quit" | grep -m1 "id name"
