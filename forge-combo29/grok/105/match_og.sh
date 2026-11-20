#!/usr/bin/env bash
# Test match: IdeaS37 on versus off, S14, 20000 nodes, openings O then G, both colours.
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DIR="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-rel/forge
FC="$HOME/fastchess/fastchess"
opts=(
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
cd /tmp
rounds=$(grep -cve '^$' "$DIR/openings_OG.epd")
"$FC" -concurrency 3 -rounds "$rounds" -games 2 \
  -openings "file=$DIR/openings_OG.epd" format=epd order=sequential \
  -pgnout "file=$DIR/match_og.pgn" notation=uci min=true append=false \
  -engine cmd="$EXE" name=s37on nodes=20000 "${opts[@]}" option.IdeaS37=true \
  -engine cmd="$EXE" name=s37off nodes=20000 "${opts[@]}" option.IdeaS37=false
