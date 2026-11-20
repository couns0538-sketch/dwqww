#!/usr/bin/env bash
# IdeaB1 on versus IdeaB1 off. S14, Threads 1, Hash 16, 20000 nodes, 553 openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
cd /tmp
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-p/forge name=IdeaB1on option.IdeaB1=true \
  -engine cmd=/tmp/forge-p/forge name=IdeaB1off option.IdeaB1=false \
  -each nodes=20000 proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$D/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -repeat -concurrency 3 \
  -ratinginterval 50 \
  -pgnout "file=$D/match_OG.pgn" notation=uci nodes=true \
  > "$D/match_OG.txt"
echo "match_exit=$?" >> "$D/match_OG.txt"
