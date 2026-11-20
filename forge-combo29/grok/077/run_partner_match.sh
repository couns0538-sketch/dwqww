#!/usr/bin/env bash
# Partner switch, 300 of my R openings, both colours. My harness, their binary.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/tmp/partner-build/forge
OUT="forge-combo29/grok/$S"
OPTS="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds 300 \
  -games 2 \
  -openings file="$OUT/R.fens" format=epd order=sequential \
  -each $OPTS \
  -engine cmd="$EXE" name=on option.IdeaS44=true \
  -engine cmd="$EXE" name=off option.IdeaS44=false \
  -pgnout file="$OUT/partner_match.pgn" min=true append=false \
  -ratinginterval 100 \
  > "$OUT/partner_match_fastchess.txt" 2>&1
echo "match_exit=$?" >> "$OUT/partner_match_fastchess.txt"
