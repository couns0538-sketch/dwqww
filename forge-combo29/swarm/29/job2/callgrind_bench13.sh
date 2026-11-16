#!/usr/bin/env bash
# callgrind (valgrind) instruction profile of bench 13: exact per-function instruction counts, no perf privileges
# needed. Text output only; the callgrind file itself stays in /tmp and is NOT committed.
set -u
EXE="$1"
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' > /tmp/cg_in.txt
valgrind --tool=callgrind --callgrind-out-file=/tmp/callgrind.out.bench13 --cache-sim=no --branch-sim=no \
  "$EXE" < /tmp/cg_in.txt > /tmp/cg_stdout.txt 2>/tmp/cg_stderr.txt
echo "valgrind exit=$?"
callgrind_annotate --threshold=95 --inclusive=no /tmp/callgrind.out.bench13 2>/dev/null | sed -n '1,60p'
