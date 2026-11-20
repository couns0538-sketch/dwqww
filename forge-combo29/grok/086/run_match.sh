#!/usr/bin/env bash
# Test match: IdeaA5 true vs IdeaA5 false. S14, Threads 1, Hash 16, 20000 nodes.
# Usage: run_match.sh EXE OPENINGS ROUNDS OUT_PREFIX
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT="$4"
FAST=/tmp/fastchess/fastchess
"$FAST" \
  -engine cmd="$EXE" name=IdeaA5on option.IdeaA5=true \
  -engine cmd="$EXE" name=IdeaA5off option.IdeaA5=false \
  -each option.Threads=1 option.Hash=16 nodes=20000 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 -ratinginterval 50 \
  -pgnout file="${OUT}.pgn" nodes=true min=false \
  -recover
