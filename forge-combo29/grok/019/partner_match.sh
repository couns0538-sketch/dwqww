#!/usr/bin/env bash
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/tmp/pwt/forge-combo29/build-rel/forge
FC=/tmp/fastchess/fastchess
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
  -openings file="$DIR/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 \
  -concurrency 3 \
  -ratinginterval 300 \
  -pgnout file="$DIR/partner_match.pgn" notation=uci nodes=true \
  > "$DIR/partner_match.log" 2>&1
echo "fastchess_exit $?" >> "$DIR/partner_match.log"
