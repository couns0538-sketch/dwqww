#!/usr/bin/env bash
# fastchess: IdeaS20 on vs off, S14, Threads 1, Hash 16, 20000 nodes.
# Openings file is argv1, rounds argv2, log argv3, pgn argv4.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-rel/forge
FC=/tmp/fastchess/fastchess
OPEN="$1"
ROUNDS="$2"
LOG="$3"
PGN="$4"
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
"$FC" \
  -engine cmd="$EXE" name=on nodes=20000 option.IdeaS20=true "${S14[@]}" \
  -engine cmd="$EXE" name=off nodes=20000 option.IdeaS20=false "${S14[@]}" \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 \
  -concurrency 3 \
  -ratinginterval 200 \
  -pgnout file="$PGN" notation=uci nodes=true \
  > "$LOG" 2>&1
echo "fastchess_exit $?" >> "$LOG"
