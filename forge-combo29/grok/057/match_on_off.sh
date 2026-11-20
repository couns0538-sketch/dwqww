#!/usr/bin/env bash
# IdeaS31 on versus off. Same exe, S14, Threads 1, Hash 16, 20000 nodes.
# Openings OG.epd (O then G, 553). Both colours. Concurrency = nproc - 1.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
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
  option.IdeaS31_Margin=80
)
"$FC" \
  -engine cmd="$EXE" name=IdeaS31on proto=uci "${S14[@]}" option.IdeaS31=true \
  -engine cmd="$EXE" name=IdeaS31off proto=uci "${S14[@]}" option.IdeaS31=false \
  -each nodes=20000 \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds 553 -repeat \
  -concurrency 3 \
  -output format=fastchess \
  -ratinginterval 100 \
  -pgnout file="$DIR/match_on_off.pgn" notation=uci \
  > "$DIR/match_on_off.log" 2>&1
echo "fastchess_exit $?" >> "$DIR/match_on_off.log"
