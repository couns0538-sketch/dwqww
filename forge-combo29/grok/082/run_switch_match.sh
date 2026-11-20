#!/usr/bin/env bash
# run_switch_match.sh EXE OPENINGS ROUNDS OUT OPTION
# OPTION is the check name. On engine gets true, off engine gets false.
# S14, Threads 1, Hash 16, 20000 nodes, both colours, concurrency 3.
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT="$4"
OPTION="$5"
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
  -engine cmd="$EXE" name=switchon "${OPTS[@]}" "option.${OPTION}=true" \
  -engine cmd="$EXE" name=switchoff "${OPTS[@]}" "option.${OPTION}=false" \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="${OUT}.pgn" notation=uci nodes=true min=true \
  > "${OUT}.log" 2>&1
echo EXIT:$?
tail -n 12 "${OUT}.log"
