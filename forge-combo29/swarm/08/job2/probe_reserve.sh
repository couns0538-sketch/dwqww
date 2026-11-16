#!/usr/bin/env bash
# probe_reserve.sh EXE OUT — what the engine does when the clock is at or below Move Overhead.
# Reserve empty is the plan_clock_budget branch `if (time <= overhead) return reserve_empty`.
set -u
EXE="$1"; OUT="$2"
: > "$OUT"
FEN="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
for clock in 10 1 0; do
  {
    echo "=========== wtime/btime $clock inc 0, default Move Overhead 10 ==========="
    printf 'uci\nisready\nucinewgame\nisready\n'
    printf 'position fen %s\nisready\n' "$FEN"
    printf 'go wtime %d btime %d\n' "$clock" "$clock"
    printf 'isready\nquit\n'
  } | "$EXE" | grep -vE '^option name|^id |^uciok' | sed "s/^/[$clock] /"
  echo
  echo "=========== wtime/btime $clock, Move Overhead 0 ==========="
  {
    printf 'uci\nsetoption name Move Overhead value 0\nisready\nucinewgame\nisready\n'
    printf 'position fen %s\nisready\n' "$FEN"
    printf 'go wtime %d btime %d\n' "$clock" "$clock"
    printf 'isready\nquit\n'
  } | "$EXE" | grep -vE '^option name|^id |^uciok' | sed "s/^/[$clock mo0] /"
  echo
done >> "$OUT"
cat "$OUT"
