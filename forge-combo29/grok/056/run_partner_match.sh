#!/usr/bin/env bash
# Partner's IdeaS34, on versus off, 300 of my R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT=forge-combo29/grok/$S
wc -l "$OUT/R.fens"
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-partner/forge name=on proto=uci \
    option.IdeaS34=true \
    option.IdeaS34_None=2 \
    option.IdeaS34_After=1 \
    option.IdeaS34_Stop=4 \
    option.IdeaS34_Bare=2 \
  -engine cmd=/tmp/forge-partner/forge name=off proto=uci \
    option.IdeaS34=false \
  -each nodes=20000 option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 \
    option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 \
    option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 \
    option.SingularDepth=6 \
    option.IirDepth=2 \
    option.NonPawnCorrection=true \
  -openings file="$OUT/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -ratinginterval 100 \
  -pgnout file="$OUT/partner_match.pgn" notation=uci
