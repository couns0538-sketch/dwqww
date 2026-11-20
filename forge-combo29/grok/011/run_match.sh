#!/usr/bin/env bash
# IdeaS25 on versus off, S14, 20000 nodes, openings O then G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
cat /tmp/kimi/first200.fens /tmp/kimi/set_G.epd > "$DIR/openings_OG.epd"
wc -l "$DIR/openings_OG.epd"
exec /tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-P/forge name=on proto=uci option.IdeaS25=true \
  -engine cmd=/tmp/forge-P/forge name=off proto=uci option.IdeaS25=false \
  -each nodes=20000 proto=uci \
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
    option.Hash=16 \
    option.Threads=1 \
  -openings "file=$DIR/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout "file=$DIR/match_on_off.pgn" notation=uci \
  -event grok-011-IdeaS25 -site local \
  -ratinginterval 100
