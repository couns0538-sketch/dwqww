#!/usr/bin/env bash
# Partner patch, IdeaA8 on versus off, 300 R openings, both colours.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/agent/repos/fastchess/fastchess
exec "$FC" \
  -engine cmd="$EXE" name=PartnerOn option.IdeaA8=true \
  -engine cmd="$EXE" name=PartnerOff option.IdeaA8=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/R.fen" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$DIR/partner_match.pgn" notation=uci \
  -ratinginterval 100 \
  -site grok-039-partner-089
