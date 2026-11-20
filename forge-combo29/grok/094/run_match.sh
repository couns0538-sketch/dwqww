#!/usr/bin/env bash
# IdeaK5 on versus IdeaK5 off. S14, Threads 1, Hash 16, 20000 nodes, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/work/build/forge
FC=/home/ubuntu/src/fastchess/fastchess
cat "$D/O_first200.fens" "$D/G_set.epd" > "$D/match_OG.epd"
"$FC" \
  -engine cmd="$EXE" name=IdeaK5on \
    option.IdeaK5=true option.IdeaK5_Divisor=64 option.IdeaK5_Depth=5 \
  -engine cmd="$EXE" name=IdeaK5off \
    option.IdeaK5=false \
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
  -openings file="$D/match_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$D/match_on_off.pgn" notation=uci nodes=true min=true \
  > "$D/match_on_off.log" 2>&1
echo MATCH_EXIT:$? >> "$D/match_on_off.log"
