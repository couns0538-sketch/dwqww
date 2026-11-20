#!/usr/bin/env bash
# Partner switch, 300 of my R openings, both colours. My harness invocation, their option names.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/build-partner/forge
cd "$DIR"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=P021on option.IdeaS26=true option.IdeaS26_Floor=7 option.IdeaS26_OrderDepth=6 \
  -engine cmd="$EXE" name=P021off option.IdeaS26=false option.IdeaS26_Floor=7 option.IdeaS26_OrderDepth=6 \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/R300.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/partner_match.pgn" notation=uci \
  -ratinginterval 100
