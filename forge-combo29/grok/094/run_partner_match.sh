#!/usr/bin/env bash
# Partner 044 IdeaK5 on versus off. Their defaults (divisor 48). 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/partner/build/forge
FC=/home/ubuntu/src/fastchess/fastchess
"$FC" \
  -engine cmd="$EXE" name=PartnerOn option.IdeaK5=true \
  -engine cmd="$EXE" name=PartnerOff option.IdeaK5=false \
  -each \
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
    option.Threads=1 \
    option.Hash=16 \
    option.OwnBook=false \
    nodes=20000 \
  -openings file="$D/R_positions.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$D/partner_match.pgn" notation=uci nodes=true min=true \
  > "$D/partner_match.log" 2>&1
echo MATCH_EXIT:$? >> "$D/partner_match.log"
