#!/usr/bin/env bash
# Partner 084's IdeaA3, true vs false, on the build of their patch. 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/grok-build/p084/forge
FC=/tmp/fastchess/fastchess
OPENINGS="$(cat ~/grok_repo.txt)/$DIR/R_300.fens"
mkdir -p /tmp/grok-match-p084
cd /tmp/grok-match-p084
EACH=(
  nodes=20000
  option.Hash=16
  option.Threads=1
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
)
"$FC" \
  -engine cmd="$EXE" name=on proto=uci option.IdeaA3=true \
  -engine cmd="$EXE" name=off proto=uci option.IdeaA3=false \
  -each "${EACH[@]}" \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=$(cat ~/grok_repo.txt)/$DIR/match_P084.pgn" notation=uci \
  -autosaveinterval 0 \
  > "$(cat ~/grok_repo.txt)/$DIR/match_P084.log" 2>&1
echo "exit $?"
tail -n 15 "$(cat ~/grok_repo.txt)/$DIR/match_P084.log"
