#!/usr/bin/env bash
# IdeaS5 on versus IdeaS5 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings are match_OG.epd (O then G, 553). Both colours: -games 2.
# Concurrency is cores minus 1.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/grok014/fastchess/fastchess
OUT="forge-combo29/grok/$S/match_fastchess.txt"
PGN="forge-combo29/grok/$S/match_fastchess.pgn"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -ge 1 ] || CONC=1
EACH="nodes=20000 option.Hash=16 option.Threads=1 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
"$FC" \
  -engine cmd="$EXE" name=IdeaS5on option.IdeaS5=true \
  -engine cmd="$EXE" name=IdeaS5off option.IdeaS5=false \
  -each $EACH \
  -openings file="forge-combo29/grok/$S/match_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency "$CONC" \
  -ratinginterval 50 \
  -pgnout file="$PGN" \
  > "$OUT" 2>&1
echo "match_exit=$?" >> "$OUT"
