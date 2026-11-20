#!/usr/bin/env bash
# Partner build, IdeaS44 on versus off, 300 of my R openings, both colours.
set -u
OUT="$(cd "$(dirname "$0")" && pwd)"
EXE=/tmp/pwork/forge-combo29/build/forge
exec "$HOME/fastchess/fastchess" \
  -engine cmd="$EXE" name=p077on option.IdeaS44=true \
  -engine cmd="$EXE" name=p077off option.IdeaS44=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$OUT/partner_match.pgn"
