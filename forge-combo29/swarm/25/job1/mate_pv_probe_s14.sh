#!/usr/bin/env bash
# mate_pv_probe_s14.sh EXE OUTFILE : the mate -12 position at depths 10..16 WITH S14, fresh process each.
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
for d in 10 11 12 13 14 15 16; do
  echo "=== depth $d (S14) ===" >> "$OUT"
  { printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value 16\nisready\n'
    printf '%s\n' "$S14"
    printf 'isready\nucinewgame\nisready\nposition fen %s\ngo depth %s\n' "$FEN" "$d"
    sleep 8; printf 'quit\n'; } \
    | "$EXE" 2>&1 | grep -E '^(info depth|bestmove)' >> "$OUT"
done
grep -E '===|score mate |bestmove' "$OUT"
