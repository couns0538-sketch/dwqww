#!/usr/bin/env bash
# repro_mate12.sh EXE OUT : one command that shows S-F1 again, self-contained.
# Runs the position at depth 12 with S14 and prints the offending info line.
set -u
EXE="$1"; OUT="$2"
FEN='8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1'
{ printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value 16\nisready\n'
  printf 'setoption name LmrQuietBase value 93\nsetoption name LmrQuietDivisor value 205\n'
  printf 'setoption name LmrNoisyBase value 13\nsetoption name LmrNoisyDivisor value 333\n'
  printf 'setoption name LmrHistoryDivisor value 5643\nsetoption name NullMoveBase value 5\n'
  printf 'setoption name LmpBase value 8\nsetoption name HistoryPruneMultiplier value 2220\n'
  printf 'setoption name HistoryBonusQuadratic value 24\nsetoption name HistoryBonusLinear value 54\n'
  printf 'setoption name HistoryBonusMax value 2212\nsetoption name SingularDepth value 6\n'
  printf 'setoption name IirDepth value 2\nsetoption name NonPawnCorrection value true\n'
  printf 'isready\nucinewgame\nisready\nposition fen %s\ngo depth 12\n' "$FEN"
  sleep 8; printf 'quit\n'; } | "$EXE" 2>&1 | grep -E '^(info depth 12|bestmove)' > "$OUT"
cat "$OUT"
