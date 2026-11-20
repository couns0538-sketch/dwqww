#!/usr/bin/env bash
# Partner switch: HindsightDepth on versus off, 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/partner/build/forge
FC=/tmp/fastchess/fastchess
OUT="$D/partner_match_R.log"
PGN="$D/partner_match_R.pgn"
rm -f "$PGN"
"$FC" \
  -engine cmd="$EXE" name=HDon option.HindsightDepth=true \
  -engine cmd="$EXE" name=HDoff option.HindsightDepth=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/sets/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$PGN" notation=uci \
  > "$OUT" 2>&1
echo "exit $?" >> "$OUT"
