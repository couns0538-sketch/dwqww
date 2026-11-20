#!/usr/bin/env bash
# Match IdeaK1 on versus off. S14, Threads 1, Hash 16, 20000 nodes.
# Usage: run_match.sh ROUNDS LOG PGN
set -u
ROUNDS="$1"
LOG="$2"
PGN="$3"
EXE=/agent/repos/work/forge-combo29/build/forge
FC="$HOME/fastchess/fastchess"
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
)
DIR=$(cd "$(dirname "$0")" && pwd)
"$FC" \
  -engine cmd="$EXE" name=on proto=uci tc=inf nodes=20000 "${S14[@]}" option.IdeaK1=true option.IdeaK1_Margin=120 \
  -engine cmd="$EXE" name=off proto=uci tc=inf nodes=20000 "${S14[@]}" option.IdeaK1=false option.IdeaK1_Margin=120 \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$PGN" notation=uci \
  > "$LOG" 2>&1
echo "exit $?" >> "$LOG"
