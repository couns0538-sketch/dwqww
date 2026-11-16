#!/usr/bin/env bash
# hash_probe.sh EXE OUT : does the bogus mate -12 depend on the transposition table size?
# Same position, depth 12, S14, but Hash 1 / 8 / 16 / 64 / 256, fresh process each.
set -u
EXE="$1"; OUT="$2"; : > "$OUT"
FEN='8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1'
for h in 1 8 16 64 256; do
  echo "=== depth 12, Hash $h MB (S14) ===" >> "$OUT"
  { printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value %s\nisready\n' "$h"
    printf 'setoption name LmrQuietBase value 93\nsetoption name LmrQuietDivisor value 205\n'
    printf 'setoption name LmrNoisyBase value 13\nsetoption name LmrNoisyDivisor value 333\n'
    printf 'setoption name LmrHistoryDivisor value 5643\nsetoption name NullMoveBase value 5\n'
    printf 'setoption name LmpBase value 8\nsetoption name HistoryPruneMultiplier value 2220\n'
    printf 'setoption name HistoryBonusQuadratic value 24\nsetoption name HistoryBonusLinear value 54\n'
    printf 'setoption name HistoryBonusMax value 2212\nsetoption name SingularDepth value 6\n'
    printf 'setoption name IirDepth value 2\nsetoption name NonPawnCorrection value true\n'
    printf 'isready\nucinewgame\nisready\nposition fen %s\ngo depth 12\n' "$FEN"
    sleep 8; printf 'quit\n'; } | "$EXE" 2>&1 | grep -E '^info depth 12' >> "$OUT"
done
cat "$OUT"
