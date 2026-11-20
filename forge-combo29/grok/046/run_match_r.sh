#!/usr/bin/env bash
# No partner branch after the 10 minute wait. Second match of this patch:
# 300 R openings, both colours, 600 games. Same S14 and node limit.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
N=$(grep -c . "$DIR/R.fen")
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
echo "openings $N concurrency $CONC no_partner" | tee "$DIR/match_r.log"
echo "NOW $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$DIR/match_r.log"
/tmp/fastchess/fastchess \
  -engine name=K7on cmd=/tmp/forge-p-build/forge option.IdeaK7=true option.IdeaK7_Weight=100 \
  -engine name=K7off cmd=/tmp/forge-p-build/forge option.IdeaK7=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$DIR/R.fen" format=epd order=sequential \
  -rounds "$N" -games 2 -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout "file=$DIR/match_r.pgn" notation=uci min=true \
  >> "$DIR/match_r.log" 2>&1
echo "fastchess_exit $?" >> "$DIR/match_r.log"
