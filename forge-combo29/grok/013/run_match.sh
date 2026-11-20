#!/usr/bin/env bash
# IdeaS13 on versus off. S14, Threads 1, Hash 16, 20000 nodes, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
cat "$DIR/O.fens" "$DIR/G.epd" > "$DIR/OG.epd"
S14=(
  option.LmrQuietBase=93
  option.LmrQuietDivisor=205
  option.LmrNoisyBase=13
  option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643
  option.NullMoveBase=5
  option.LmpBase=8
  option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24
  option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212
  option.SingularDepth=6
  option.IirDepth=2
  option.NonPawnCorrection=true
  option.Threads=1
  option.Hash=16
)
SPINS=(
  option.IdeaS13_Lag=4
  option.IdeaS13_Bonus=160
  option.IdeaS13_Divisor=48
  option.IdeaS13_Shave=1
)
exec "$FC" \
  -engine cmd="$EXE" name=on option.IdeaS13=true "${SPINS[@]}" "${S14[@]}" \
  -engine cmd="$EXE" name=off option.IdeaS13=false "${SPINS[@]}" "${S14[@]}" \
  -each nodes=20000 proto=uci \
  -openings "file=${DIR}/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=${DIR}/match_on_off.pgn" nodes=true
