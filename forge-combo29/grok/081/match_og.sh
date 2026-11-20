#!/usr/bin/env bash
# IdeaS10 on versus IdeaS10 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G (553). -repeat plays both colours: 1106 games.
# Concurrency is cores minus 1.
set -u
S=$(cat "$HOME/grok_seat.txt")
REPO=$(cat "$HOME/grok_repo.txt")
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-build/work/forge
FC=/tmp/src/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
echo "concurrency $CONC cores $CORES" | tee "$DEST/match_og.txt"
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
  -openings file="$DEST/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -repeat \
  -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout file="$DEST/match_og.pgn" notation=uci \
  >> "$DEST/match_og.txt" 2>&1
echo "fastchess_exit $?" >> "$DEST/match_og.txt"
tail -n 30 "$DEST/match_og.txt"
