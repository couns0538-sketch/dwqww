#!/usr/bin/env bash
set -u
EXE="$1"
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
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false"
for b in 11 13; do
  { printf 'uci\nisready\nsetoption name Threads value 1\nisready\nsetoption name Hash value 16\nisready\n'
    printf '%s\n' "$S14"
    printf 'isready\nucinewgame\nisready\nbench %s\nquit\n' "$b"; } | "$EXE" 2>&1 | grep -E 'bench depth|unknown option|invalid value'
done
