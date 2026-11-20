#!/usr/bin/env bash
# Partner IdeaB1 on versus off. 300 R openings, both colours, S14, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-partner/forge name=PartnerOn option.IdeaB1=true \
  -engine cmd=/tmp/forge-partner/forge name=PartnerOff option.IdeaB1=false \
  -each nodes=20000 proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$D/R.epd" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=$D/partner_match_R.pgn" notation=uci \
  > "$D/partner_match_R.txt"
echo "match_exit=$?" >> "$D/partner_match_R.txt"
