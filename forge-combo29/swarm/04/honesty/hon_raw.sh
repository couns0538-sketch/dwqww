#!/usr/bin/env bash
set -u
EXE=/home/ubuntu/builds/rel/forge
for b in 11 13 16; do
  printf 'uci\nisready\nbench %s\nquit\n' "$b" | "$EXE" > raw_bench$b.txt 2>&1
done
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | "$EXE" > raw_perft5.txt 2>&1
