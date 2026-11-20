#!/usr/bin/env bash
# Partner 061 IdeaS25, on versus off, 300 R openings, both colours. My harness, not theirs.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
cd /tmp
exec /tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-Partner/forge name=on proto=uci option.IdeaS25=true \
  -engine cmd=/tmp/forge-Partner/forge name=off proto=uci option.IdeaS25=false \
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
  -openings "file=$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout "file=$DIR/partner_match.pgn" notation=uci \
  -event grok-011-partner-061 -site local \
  -ratinginterval 300
