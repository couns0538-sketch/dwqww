#!/usr/bin/env bash
# callgrind on the FORGE_PORTABLE build. Reason: valgrind 3.22 cannot decode AVX-512, so the lock build dies with
# SIGILL under it. The portable build has the SAME node counts (bench 11/13/16, perft 5 identical) and is only used
# for instruction-count ATTRIBUTION; absolute times from it are not used anywhere.
set -u
EXE="$1"
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' > /tmp/cg_in.txt
valgrind --tool=callgrind --callgrind-out-file=/tmp/callgrind.out.portable --cache-sim=no --branch-sim=no \
  "$EXE" < /tmp/cg_in.txt > /tmp/cg_stdout2.txt 2>/tmp/cg_stderr2.txt
echo "valgrind exit=$?"
callgrind_annotate --threshold=99.5 --inclusive=no /tmp/callgrind.out.portable 2>/dev/null | sed -n '1,45p'
