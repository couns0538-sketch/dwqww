#!/usr/bin/env bash
# Partner 055 engine, IdeaS37 true vs false, 300 R openings, both colours.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
EXE=/tmp/partner-055/forge-combo29/build-rel/forge
FC=/tmp/fastchess/fastchess
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=S37on proto=uci option.IdeaS37=true \
  -engine cmd="$EXE" name=S37off proto=uci option.IdeaS37=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/openings_R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$DIR/partner055_match.pgn" notation=uci nodes=true \
  > "$DIR/partner055_match.txt" 2>&1
echo "exit $?" >> "$DIR/partner055_match.txt"
