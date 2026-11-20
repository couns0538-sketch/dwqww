#!/usr/bin/env bash
# K11 on versus K11 off. S14, Threads 1, Hash 16, 20000 nodes, O and G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
OUT="$REPO/forge-combo29/grok/$S"
cd /tmp/match050
rm -f config.json
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-p/forge name=K11on option.IdeaK11=true \
  -engine cmd=/tmp/forge-p/forge name=K11off option.IdeaK11=false \
  -each option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true nodes=20000 \
  -openings "file=$OUT/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=$OUT/match_og.pgn" notation=uci \
  > "$OUT/match_og.out" 2>&1
echo EXIT:$? >> "$OUT/match_og.out"
