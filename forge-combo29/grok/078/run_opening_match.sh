#!/bin/bash
# Match of one binary, switch true vs false, over a FEN file, both colours.
# Usage: run_opening_match.sh EXE FENS ROUNDS OUT_PREFIX OPTION
set -u
EXE="$1"
FENS="$2"
ROUNDS="$3"
OUT="$4"
OPTION="$5"
OPTS="option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds "$ROUNDS" \
  -repeat \
  -openings file="$FENS" format=epd order=sequential \
  -engine cmd="$EXE" name=on nodes=20000 option."$OPTION"=true $OPTS \
  -engine cmd="$EXE" name=off nodes=20000 option."$OPTION"=false $OPTS \
  -pgnout file="${OUT}.pgn" notation=uci \
  > "${OUT}.log" 2>&1
echo "match_exit $?" >> "${OUT}.log"
