#!/bin/bash
# honesty numbers for one sanitizer build: go bench 11/13/16 (the argument is DEPTH) + startpos perft 5
exe="$1"; out="$2"
run_bench() {
  printf 'uci\nisready\nucinewgame\nisready\nsetoption name Threads value 1\ngo bench %s\nquit\n' "$1" \
    | env -u TSAN_OPTIONS "$exe" 2>/dev/null | grep "info string bench" | sed "s/^/bench$1 /"
}
{
  run_bench 11
  run_bench 13
  run_bench 16
  printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | env -u TSAN_OPTIONS "$exe" 2>/dev/null | grep -E "^nodes" | sed "s/^/perft5 /"
} > "$out" 2>&1
