#!/usr/bin/env bash
# probe_reserve.sh EXE OUT — what the engine does when the clock is at or below Move Overhead.
#
# CORRECTED (seat 19's finding 19-F12 broadcast): the first version of this script piped `isready`+`quit` into
# the engine right after `go`, which makes this build answer a FABRICATED `bestmove` with no `info` line. Its
# committed output is kept as probe_reserve_v1_INVALID.txt, evidence of the mistake.
# This version reads stdout until `bestmove` arrives and only then closes the engine: nothing is sent while a
# search is running.
set -u
EXE="$1"; OUT="$2"
: > "$OUT"
FEN="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

probe () {  # $1 label, $2 go line, $3 optional setoption line
  local label="$1" goline="$2" opts="${3:-}"
  {
    printf 'uci\nisready\n'
    [ -n "$opts" ] && printf '%s\n' "$opts"
    printf 'ucinewgame\nisready\nposition fen %s\nisready\n' "$FEN"
    printf '%s\n' "$goline"
    while IFS= read -r line; do
      printf '%s\n' "$line"
      case "$line" in bestmove*) break;; esac
    done
    printf 'isready\nquit\n'
  } | "$EXE" | grep -E '^info depth|^info string|^bestmove' | sed "s/^/[$label] /" | tee -a "$OUT"
  echo >> "$OUT"
}

echo "=== reserve-empty branch: clock at or below Move Overhead (default 10) ===" >> "$OUT"
probe "wtime10" "go wtime 10 btime 10"
probe "wtime1"  "go wtime 1 btime 1"
probe "wtime0"  "go wtime 0 btime 0"
echo "=== same clocks with Move Overhead 0, so the reserve is not empty ===" >> "$OUT"
probe "wtime10_mo0" "go wtime 10 btime 10" "setoption name Move Overhead value 0"
probe "wtime1_mo0"  "go wtime 1 btime 1"   "setoption name Move Overhead value 0"
cat "$OUT"
