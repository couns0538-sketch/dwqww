#!/usr/bin/env bash
# Partner patch, switch on versus off, 300 of my R openings, both colours (600 games).
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-build/partner/forge
FC=/tmp/src/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
echo "concurrency $CONC cores $CORES" | tee "$DEST/partner_match.txt"
"$FC" \
  -engine cmd="$EXE" name=s10on option.IdeaS10=true \
  -engine cmd="$EXE" name=s10off option.IdeaS10=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 \
    option.NonPawnCorrection=true \
  -openings file="$DEST/R.epd" format=epd order=sequential \
  -rounds 300 -repeat \
  -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout file="$DEST/partner_match.pgn" notation=uci \
  >> "$DEST/partner_match.txt" 2>&1
echo "fastchess_exit $?" >> "$DEST/partner_match.txt"
tail -n 20 "$DEST/partner_match.txt"
