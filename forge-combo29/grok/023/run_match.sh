#!/usr/bin/env bash
# IdeaS29 on versus off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings file is argv 1. Rounds must equal the number of openings.
# Games 2 = both colours. Concurrency is cores minus 1.
set -u
OPENINGS="$1"
ROUNDS="$2"
OUT="$3"
EXE="$4"
FC="${5:-/tmp/fastchess/fastchess}"
PROFILE="${6:-self}"
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
)
if [ "$PROFILE" = "divisor" ]; then
  ON_OPTS=(option.IdeaS29=true option.IdeaS29_Threshold=0 option.IdeaS29_Divisor=8)
  OFF_OPTS=(option.IdeaS29=false option.IdeaS29_Threshold=0 option.IdeaS29_Divisor=8)
elif [ "$PROFILE" = "self" ]; then
  ON_OPTS=(option.IdeaS29=true option.IdeaS29_Threshold=0 option.IdeaS29_Scale=1)
  OFF_OPTS=(option.IdeaS29=false option.IdeaS29_Threshold=0 option.IdeaS29_Scale=1)
else
  echo "bad profile $PROFILE" >&2
  exit 2
fi
"$FC" \
  -engine cmd="$EXE" name=IdeaS29-on "${ON_OPTS[@]}" \
  -engine cmd="$EXE" name=IdeaS29-off "${OFF_OPTS[@]}" \
  -each nodes=20000 option.Hash=16 option.Threads=1 "${S14[@]}" \
  -openings "file=$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -repeat \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=${OUT}.pgn" notation=uci min=true \
  -config "outname=${OUT}.fastchess.json" \
  > "${OUT}.txt" 2>&1
echo "match_exit=$?" >> "${OUT}.txt"
