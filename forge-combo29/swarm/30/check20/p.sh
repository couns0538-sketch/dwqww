#!/usr/bin/env bash
# Third independent data point on 10-F64's board: exact command and FEN as seat 10 states them.
# Prints every info line's depth/nodes so intermediate and final counts are distinguishable.
EXE=/home/ubuntu/b/pc/forge
FEN="5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1"
{
  echo "exe: $EXE"
  sha256sum "$EXE"
  echo "fen: $FEN"
  echo "cmd: go depth 22   (Threads 1, Hash 16, PC20, interactive reader)"
  date -u
} > meta.txt
{
  printf 'uci\nisready\n'
  for o in "LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333" "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220" "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212" "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true" "CuckooRep true" "HistRework 2" "TtPruneV2 true" "CorrHistV2 true" "MateAlphaGuard true" "OwnBook false"; do
    printf 'setoption name %s\nisready\n' "$o"
  done
  printf 'ucinewgame\nisready\nposition fen %s\nisready\ngo depth 22\n' "$FEN"
  sleep 100
  printf 'stop\nisready\nquit\n'
} | timeout 150 "$EXE" > raw.txt 2>&1
date -u >> meta.txt
