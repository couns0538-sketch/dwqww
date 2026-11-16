#!/usr/bin/env bash
# honesty.sh EXE OUTFILE : runs the four honesty checks, one fresh process per line.
set -u
EXE="$1"
OUT="$2"
: > "$OUT"
run() {
  local tag="$1"; shift
  echo "=== $tag ===" >> "$OUT"
  printf '%s\nquit\n' "$1" | "$EXE" 2>&1 | tee -a "$OUT" | grep -E 'nodes|bestmove|perft' | tail -3
  echo "---" >> "$OUT"
}
run "bench 11" "bench 11"
run "bench 13" "bench 13"
run "bench 16" "bench 16"
echo "=== perft 5 ===" >> "$OUT"
printf 'position startpos\ngo perft 5\nquit\n' | "$EXE" 2>&1 | tee -a "$OUT" | tail -3
echo "---" >> "$OUT"
