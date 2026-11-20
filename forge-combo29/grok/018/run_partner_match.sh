#!/usr/bin/env bash
# Partner seat 068 build, IdeaS16 on versus off, 300 R openings, both colours.
set -u
OPEN=$1
ROUNDS=$2
OUT=$3
CONC=$4
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
"$FC" \
  -engine cmd="$EXE" name=s16on option.IdeaS16=true \
  -engine cmd="$EXE" name=s16off option.IdeaS16=false \
  -each nodes=20000 proto=uci \
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
  -openings "file=$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" \
  -games 2 \
  -concurrency "$CONC" \
  -pgnout "file=${OUT}.pgn" nodes=true \
  -ratinginterval 50
