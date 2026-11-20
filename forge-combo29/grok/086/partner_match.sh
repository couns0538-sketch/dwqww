#!/usr/bin/env bash
# Partner switch, 300 R openings, both colours. Harness is this script, not the partner's.
set -u
EXE="$1"
OPENINGS="$2"
OUT="$3"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on option.IdeaS36=true \
  -engine cmd="$EXE" name=off option.IdeaS36=false \
  -each option.Threads=1 option.Hash=16 nodes=20000 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="${OUT}.pgn" nodes=true \
  -recover
