#!/usr/bin/env bash
# callgrind on the portable+(-g) build, then a LINE-level report for the three hottest functions.
# The -g build has the same source and the same node counts (checked below); it exists only so callgrind can name
# source lines. Times from it are never used.
set -u
EXE="$1"
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 11\nquit\n' > /tmp/cgl_in.txt
"$EXE" < /tmp/cgl_in.txt | grep "bench depth"          # node-count check of this build
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' > /tmp/cgl_in.txt
valgrind --tool=callgrind --callgrind-out-file=/tmp/callgrind.out.lines --cache-sim=no "$EXE" < /tmp/cgl_in.txt > /dev/null 2>&1
echo "valgrind exit=$?"
for fn in "evaluate_position" "Worker::search" "apply_and_evaluate"; do
  echo "===== $fn ====="
  callgrind_annotate --auto=yes --threshold=40 /tmp/callgrind.out.lines 2>/dev/null | grep -A400 "$fn" | grep -E "^ *[0-9,]{9,}" | sort -t'(' -k2 -nr | head -12
done
