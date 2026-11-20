#!/usr/bin/env bash
# Partner patch, IdeaK6 on vs off, 300 of my R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
BOOK="$(pwd)/$DIR/R300.fens"
PGN="$(pwd)/$DIR/partner_match.pgn"
OUT="$(pwd)/$DIR/partner_match.txt"
OPTS=(
  option.Threads=1
  option.Hash=16
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
  nodes=20000
)
mkdir -p /tmp/match-partner
cd /tmp/match-partner
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaK6on option.IdeaK6=true "${OPTS[@]}" \
  -engine cmd="$EXE" name=IdeaK6off option.IdeaK6=false "${OPTS[@]}" \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$PGN" nodes=true \
  -ratinginterval 100 \
  > "$OUT" 2>&1
echo EXIT:$? >> "$OUT"
