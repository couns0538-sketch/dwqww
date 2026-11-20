#!/usr/bin/env bash
# run_match.sh BOOK ROUNDS OUTDIR
# Both engines are the same binary. on has IdeaK4 true, off has IdeaK4 false.
set -u
BOOK=$1
ROUNDS=$2
OUT=$3
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
mkdir -p "$OUT"
cd "$OUT"
"$FC" \
  -engine cmd="$EXE" name=IdeaK4on option.IdeaK4=true option.IdeaK4_Shrink=32 \
  -engine cmd="$EXE" name=IdeaK4off option.IdeaK4=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file=games.pgn notation=uci append=false \
  -ratinginterval 50
