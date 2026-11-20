#!/usr/bin/env bash
# Partner seat 064, option IdeaS6, on versus off.
# 300 R openings, both colours, 600 games. S14, Threads 1, Hash 16, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/tmp/grok014/partner/forge-combo29/build/forge
FC=/tmp/grok014/fastchess/fastchess
OUT="forge-combo29/grok/$S/partner_match.txt"
PGN="forge-combo29/grok/$S/partner_match.pgn"
CONC=$(( $(nproc) - 1 ))
[ "$CONC" -ge 1 ] || CONC=1
EACH="nodes=20000 option.Hash=16 option.Threads=1 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
"$FC" \
  -engine cmd="$EXE" name=IdeaS6on option.IdeaS6=true \
  -engine cmd="$EXE" name=IdeaS6off option.IdeaS6=false \
  -each $EACH \
  -openings file="forge-combo29/grok/$S/R.fen" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency "$CONC" \
  -ratinginterval 50 \
  -pgnout file="$PGN" \
  > "$OUT" 2>&1
echo "match_exit=$?" >> "$OUT"
