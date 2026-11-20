#!/usr/bin/env bash
# run_match.sh EXE OPENINGS ROUNDS OUT_PREFIX
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT="$4"
FC=/tmp/fastchess/fastchess
OPTS=(
  proto=uci nodes=20000
  option.Threads=1 option.Hash=16
  option.LmrQuietBase=93 option.LmrQuietDivisor=205
  option.LmrNoisyBase=13 option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643 option.NullMoveBase=5
  option.LmpBase=8 option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212 option.SingularDepth=6
  option.IirDepth=2 option.NonPawnCorrection=true
)
"$FC" \
  -engine cmd="$EXE" name=IdeaA1on "${OPTS[@]}" option.IdeaA1=true \
  -engine cmd="$EXE" name=IdeaA1off "${OPTS[@]}" option.IdeaA1=false \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="${OUT}.pgn" notation=uci nodes=true min=true \
  > "${OUT}.log" 2>&1
echo EXIT:$?
tail -n 30 "${OUT}.log"
