#!/usr/bin/env bash
# mate_pv_probe.sh EXE OUTFILE : re-runs the mate -12 position at several depths, fresh process each.
set -u
EXE="$1"; OUT="$2"; : > "$OUT"
FEN='8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1'
for d in 10 11 12 13 14 16; do
  echo "=== depth $d ===" >> "$OUT"
  { printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value 16\nisready\nucinewgame\nisready\nposition fen %s\ngo depth %s\n' "$FEN" "$d"; sleep 6; printf 'quit\n'; } \
    | "$EXE" 2>&1 | grep -E '^(info depth|bestmove)' | tee -a "$OUT"
done
