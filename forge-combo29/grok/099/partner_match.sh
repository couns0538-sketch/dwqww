#!/usr/bin/env bash
# My harness, seat 049's engine. IdeaK10 on versus off, their defaults,
# 300 R openings, both colours, 20000 nodes, S14, Threads 1, Hash 16.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
EXE=/tmp/forge-049/forge
OUT=$REPO/forge-combo29/grok/$S/partner_match
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
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on proto=uci nodes=20000 "${S14[@]}" \
    option.IdeaK10=true option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=3072 \
  -engine cmd="$EXE" name=off proto=uci nodes=20000 "${S14[@]}" \
    option.IdeaK10=false option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=3072 \
  -openings file="$REPO/forge-combo29/grok/$S/openings/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="${OUT}.pgn" notation=uci append=false \
  > "${OUT}.txt"
echo MATCH_EXIT:$?
