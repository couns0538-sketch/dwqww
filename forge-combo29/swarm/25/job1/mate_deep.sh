#!/usr/bin/env bash
# mate_deep.sh EXE OUT : the mate -12 position at growing depths, S14, one fresh process per depth.
set -u
EXE="$1"; OUT="$2"; : > "$OUT"
FEN='8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1'
S14="setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true"
for d in 18 20 22 24 26 28; do
  echo "=== depth $d (S14, full PV line, no grep of info) ===" >> "$OUT"
  { printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value 64\nisready\n'
    printf '%s\n' "$S14"
    printf 'isready\nucinewgame\nisready\nposition fen %s\ngo depth %s\n' "$FEN" "$d"
    sleep 20; printf 'quit\n'; } \
    | "$EXE" 2>&1 | grep -E '^(info depth|bestmove)' | tail -2 >> "$OUT"
done
cat "$OUT"
