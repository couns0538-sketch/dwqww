#!/usr/bin/env bash
# Match harness. Both sides are the patched engine, S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is false on both: the embedded book would play the opening and hide the search option.
# IdeaS29 is the only difference. Openings are played once, both colours (games 2).
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=${EXE_OVERRIDE:-/agent/repos/work/forge-combo29/build/forge}
FC=/tmp/fastchess/fastchess
OPEN=$1
ROUNDS=$2
TAG=$3
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=IdeaS29_on option.IdeaS29=true \
  -engine cmd="$EXE" name=IdeaS29_off option.IdeaS29=false \
  -each nodes=20000 tc=inf option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$DIR/${TAG}.pgn" notation=uci append=false \
  -ratinginterval 100
