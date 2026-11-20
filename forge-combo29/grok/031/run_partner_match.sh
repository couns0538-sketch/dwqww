#!/usr/bin/env bash
# 300 of our R openings, both colours, partner build, their switch on versus off.
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/partner-build-081/forge
FC=/tmp/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$D"
{
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
  echo "fastchess $FC"
  sha256sum "$FC"
  echo "concurrency $CONC"
  echo "openings R300.fen both colours"
  "$FC" \
    -engine cmd="$EXE" name=on option.IdeaS10=true \
    -engine cmd="$EXE" name=off option.IdeaS10=false \
    -each nodes=20000 option.Threads=1 option.Hash=16 \
      option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
      option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
      option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
      option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
      option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
      option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    -openings file="$D/R300.fen" format=epd order=sequential \
    -rounds 300 -games 2 \
    -concurrency "$CONC" \
    -pgnout file="$D/partner081_R.pgn" notation=uci nodes=true min=true \
    -ratinginterval 100
} > "$D/partner081_R.txt" 2> "$D/partner081_R.err"
echo "match_exit $?" >> "$D/partner081_R.txt"
