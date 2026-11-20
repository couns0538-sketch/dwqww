#!/usr/bin/env bash
# Partner IdeaA1 on vs off, 300 of my R openings, both colours, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/partner-src/build/forge
FC=/tmp/fastchess/fastchess
COMMON="option.Hash=16 option.Threads=1 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=P082on option.IdeaA1=true \
  -engine cmd="$EXE" name=P082off option.IdeaA1=false \
  -each nodes=20000 $COMMON \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -repeat \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout file="$DIR/partner_match.pgn" notation=uci nodes=true append=false \
  > "$DIR/partner_match.log" 2>&1
echo "match_exit $?" >> "$DIR/partner_match.log"
