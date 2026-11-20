#!/usr/bin/env bash
# 300 of my R openings, both colours, partner build, partner defaults.
set -u
SEAT="$(cd "$(dirname "$0")" && pwd)"
EXE=/tmp/partner/forge-combo29/build/forge
FC="${HOME}/fastchess/fastchess"
"$FC" \
  -engine cmd="$EXE" name=IdeaB10On option.IdeaB10=true \
  -engine cmd="$EXE" name=IdeaB10Off option.IdeaB10=false \
  -each option.Hash=16 option.Threads=1 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
    nodes=20000 \
  -openings file="$SEAT/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$SEAT/partner_match.pgn" notation=uci \
  -ratinginterval 100
