#!/usr/bin/env bash
# Test match: IdeaK6 on vs off, S14, Threads 1, Hash 16, 20000 nodes, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/forge-P/forge
BOOK="$(pwd)/$DIR/OG553.epd"
PGN="$(pwd)/$DIR/match_on_off.pgn"
OUT="$(pwd)/$DIR/match_on_off.txt"
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
mkdir -p /tmp/match-full
cd /tmp/match-full
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaK6on option.IdeaK6=true "${OPTS[@]}" \
  -engine cmd="$EXE" name=IdeaK6off option.IdeaK6=false "${OPTS[@]}" \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout file="$PGN" nodes=true \
  -ratinginterval 100 \
  > "$OUT" 2>&1
echo EXIT:$? >> "$OUT"
