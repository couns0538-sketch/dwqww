#!/usr/bin/env bash
# 300 R openings, both colours, partner binary, IdeaB1 true vs false.
set -eu
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/partner-build/forge
FAST=/tmp/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$DIR"
"$FAST" \
  -engine cmd="$EXE" name=b1on option.IdeaB1=true \
  -engine cmd="$EXE" name=b1off option.IdeaB1=false \
  -each option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16 \
        option.OwnBook=false nodes=20000 \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/partner_match.pgn" notation=uci \
  > "$DIR/partner_match.txt" 2>&1
echo "match exit $?" >> "$DIR/partner_match.txt"
