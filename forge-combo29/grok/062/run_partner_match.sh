#!/usr/bin/env bash
# Partner engine, switch on versus off, 300 of my R openings, both colours.
set -u
D="/agent/repos/dwqww/forge-combo29/grok/062"
EXE="/tmp/partner-build/forge"
FC="/tmp/fastchess/fastchess"
"$FC" \
  -engine cmd="$EXE" name=on option.DeadMaterial=true \
  -engine cmd="$EXE" name=off option.DeadMaterial=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$D/partner012_match.pgn" notation=uci append=false \
  > "$D/partner012_match.txt" 2> "$D/partner012_match.err"
echo EXIT:$?
tail -n 20 "$D/partner012_match.txt"
grep -E 'unknown option|invalid value|illegal move|invalid FEN' "$D/partner012_match.txt" "$D/partner012_match.err" || echo NO_BAD_LINES
