#!/usr/bin/env bash
# quit_during_search.sh EXE OUT : reproduces or refutes 19-F12's "quit mid-search fabricates a bestmove".
# Three cases, same startpos depth 12:
#   A: quit IMMEDIATELY after go    (the pipelined pattern; 19-F12 says this fabricates)
#   B: quit 2 s after go            (19-F12 says this is the good pattern)
#   C: read stdout until bestmove, then quit (my run_pv.py pattern)
set -u
EXE="$1"; OUT="$2"; : > "$OUT"

echo "=== A: go depth 12, quit immediately (pipelined) ===" >> "$OUT"
printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\nquit\n' | "$EXE" 2>&1 \
  | grep -E '^(info depth|bestmove)' | tail -3 >> "$OUT"

echo "=== B: go depth 12, quit after 2 s ===" >> "$OUT"
{ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\n'; sleep 2; printf 'quit\n'; } \
  | "$EXE" 2>&1 | grep -E '^(info depth|bestmove)' | tail -3 >> "$OUT"

echo "=== C: go depth 12, read until bestmove then quit ===" >> "$OUT"
printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\n' > /tmp/qc_in.txt
{ cat /tmp/qc_in.txt; } | "$EXE" 2>&1 | grep -E '^(info depth|bestmove)' | tail -3 >> "$OUT"
cat "$OUT"
