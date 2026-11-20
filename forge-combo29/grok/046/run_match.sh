#!/usr/bin/env bash
# IdeaK7 on vs IdeaK7 off. S14, Threads 1, Hash 16, 20000 nodes.
# 553 openings (O then G), both colours, one pass: 1106 games.
# Concurrency is cores minus 1.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
cat "$DIR/first200.fens" "$DIR/set_G.epd" > "$DIR/openings_OG.epd"
N=$(grep -c . "$DIR/openings_OG.epd")
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
echo "openings $N concurrency $CONC" | tee "$DIR/match_k7.log"
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
  -openings "file=$DIR/openings_OG.epd" format=epd order=sequential \
  -rounds "$N" -games 2 -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout "file=$DIR/match_k7.pgn" notation=uci min=true \
  >> "$DIR/match_k7.log" 2>&1
echo "fastchess_exit $?" >> "$DIR/match_k7.log"
