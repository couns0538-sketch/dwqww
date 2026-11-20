#!/usr/bin/env bash
# IdeaA3 true (SeeFloor default) vs IdeaA3 false. S14, Threads 1, Hash 16, 20000 nodes.
# usage: match_on_off.sh OPENINGS ROUNDS OUT_BASENAME
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
OPENINGS="$1"
ROUNDS="$2"
BASE="$3"
EXE=/tmp/grok-build/work/forge
FC=/tmp/fastchess/fastchess
mkdir -p /tmp/grok-match
cd /tmp/grok-match
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
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -ratinginterval 50 \
  -pgnout "file=$(cat ~/grok_repo.txt)/$DIR/${BASE}.pgn" notation=uci nodes=true \
  -autosaveinterval 0 \
  > "$(cat ~/grok_repo.txt)/$DIR/${BASE}.log" 2>&1
echo "exit $?"
tail -n 40 "$(cat ~/grok_repo.txt)/$DIR/${BASE}.log"
