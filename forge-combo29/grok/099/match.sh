#!/usr/bin/env bash
# fastchess: IdeaK10 on vs IdeaK10 off. S14, Threads 1, Hash 16, 20000 nodes.
# rounds and openings file are the remaining arguments so a 1-round smoke
# test and the 553-round match share this script.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
ROUNDS=${1:-553}
OPENINGS=${2:-$REPO/forge-combo29/grok/$S/openings/OG.epd}
OUT=${3:-$REPO/forge-combo29/grok/$S/match}
EXE=/tmp/forge-P/forge
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
    option.IdeaK10=true option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=12000 \
  -engine cmd="$EXE" name=off proto=uci nodes=20000 "${S14[@]}" \
    option.IdeaK10=false \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="${OUT}.pgn" notation=uci append=false \
  > "${OUT}.txt"
echo MATCH_EXIT:$?
