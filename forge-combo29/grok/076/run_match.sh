#!/usr/bin/env bash
# Test match. Args: OPENINGS OUT_LOG PGN ROUNDS
# fastchess keeps only the first ROUNDS openings, then plays -games 2 (both colours).
# ROUNDS must equal the number of openings. Do not set it higher to repeat the list.
# Engine on (IdeaS27 true) vs engine off (IdeaS27 false). S14, Threads 1, Hash 16, 20000 nodes.
set -u
OPENINGS=$1
LOG=$2
PGN=$3
ROUNDS=${4:-1}
P=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
"$FC" \
  -engine cmd="$P" name=s27on option.IdeaS27=true \
  -engine cmd="$P" name=s27off option.IdeaS27=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$PGN" min=true append=false \
  -ratinginterval 100 \
  > "$LOG" 2>&1
echo EXIT:$?
tail -n 30 "$LOG"
