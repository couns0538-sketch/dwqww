#!/usr/bin/env bash
set -u
EXE=/tmp/partner005/forge-combo29/build-rel/forge
DIR=/agent/repos/dwqww/forge-combo29/grok/105
opts=(
  option.Threads=1 option.Hash=16
  option.LmrQuietBase=93 option.LmrQuietDivisor=205
  option.LmrNoisyBase=13 option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643 option.NullMoveBase=5
  option.LmpBase=8 option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212 option.SingularDepth=6
  option.IirDepth=2 option.NonPawnCorrection=true
)
cd /tmp
"/home/ubuntu/fastchess/fastchess" -concurrency 3 -rounds 300 -games 2 \
  -openings file=$DIR/R.fens format=epd order=sequential \
  -pgnout file=$DIR/partner005_match.pgn notation=uci min=true append=false \
  -engine cmd=$EXE name=s37on nodes=20000 "${opts[@]}" option.IdeaS37=true \
  -engine cmd=$EXE name=s37off nodes=20000 "${opts[@]}" option.IdeaS37=false
