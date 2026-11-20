#!/usr/bin/env bash
# 300 R openings, both colours, nodes 20000, S14.
# Usage: run_r_match.sh ON_EXE OFF_EXE ON_NAME OFF_NAME OUT_PREFIX [extra on-options...]
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
ON_EXE=$1
OFF_EXE=$2
ON_NAME=$3
OFF_NAME=$4
PREFIX=$5
shift 5
head -n 300 "$D/R.fens" > "$D/${PREFIX}_R300.fens"
EXTRA=""
for item in "$@"; do
  EXTRA="$EXTRA option.${item}"
done
/tmp/fastchess/fastchess \
  -engine cmd="$ON_EXE" name="$ON_NAME" option.IdeaB10=true $EXTRA \
  -engine cmd="$OFF_EXE" name="$OFF_NAME" option.IdeaB10=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.OwnBook=false \
  -openings file="$D/${PREFIX}_R300.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -resign movecount=6 score=800 twosided=true \
  -draw movenumber=50 movecount=8 score=10 \
  -maxmoves 200 \
  -pgnout file="$D/${PREFIX}.pgn" notation=uci nodes=true \
  -ratinginterval 100
