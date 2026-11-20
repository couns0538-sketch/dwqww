#!/usr/bin/env bash
# Partner exe, IdeaK1 on versus off, 300 R openings, both colours.
set -u
EXE=/tmp/partner-src/forge-combo29/build/forge
FC="$HOME/fastchess/fastchess"
DIR=$(cd "$(dirname "$0")" && pwd)
S14=(
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
  option.IdeaK1_Margin=180
  option.IdeaK1_DepthSlack=4
  option.IdeaK1_MinDepth=5
)
"$FC" \
  -engine cmd="$EXE" name=on proto=uci tc=inf nodes=20000 "${S14[@]}" option.IdeaK1=true \
  -engine cmd="$EXE" name=off proto=uci tc=inf nodes=20000 "${S14[@]}" option.IdeaK1=false \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$DIR/partner_match_r.pgn" notation=uci \
  > "$DIR/partner_match_r.log" 2>&1
echo "exit $?" >> "$DIR/partner_match_r.log"
