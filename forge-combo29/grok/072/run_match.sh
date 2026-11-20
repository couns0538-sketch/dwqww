#!/usr/bin/env bash
# IdeaS27 true vs false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours.
set -eu
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/build/forge
FC=/tmp/fastchess/fastchess
mkdir -p /tmp/fc-072
cd /tmp/fc-072
"$FC" \
  -engine cmd="$EXE" name=s27on proto=uci option.IdeaS27=true \
  -engine cmd="$EXE" name=s27off proto=uci option.IdeaS27=false \
  -openings file="$DIR/OG.fens" format=epd order=sequential \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -rounds 553 -repeat -concurrency 3 \
  -pgnout file="$DIR/match_og.pgn" \
  -ratinginterval 100 \
  > "$DIR/match_og.log" 2>&1
echo "MATCH_EXIT:$?" >> "$DIR/match_og.log"
