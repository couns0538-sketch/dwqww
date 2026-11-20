#!/usr/bin/env bash
# exe P with IdeaS34 on versus the same exe with IdeaS34 off.
# S14, Threads 1, Hash 16, 20000 nodes. Openings O then G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT=forge-combo29/grok/$S
cat /tmp/O.fens /tmp/G.epd > "$OUT/OG.epd"
wc -l "$OUT/OG.epd"
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-P/forge name=on proto=uci \
    option.IdeaS34=true \
    option.IdeaS34_EaseZero=2 \
    option.IdeaS34_EaseMid=1 \
    option.IdeaS34_Couple=2 \
    option.IdeaS34_Full=4 \
    option.IdeaS34_NoTt=2 \
  -engine cmd=/tmp/forge-P/forge name=off proto=uci \
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
  -openings file="$OUT/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -ratinginterval 50 \
  -pgnout file="$OUT/match.pgn" notation=uci
