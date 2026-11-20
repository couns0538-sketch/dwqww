#!/usr/bin/env bash
# Match: DeadMaterial on versus off, same binary, S14, 20000 nodes.
# Usage: run_match.sh ROUNDS OUTSTEM
set -u
ROUNDS="${1:?rounds}"
STEM="${2:?stem}"
D="/agent/repos/dwqww/forge-combo29/grok/062"
EXE="/agent/repos/work/forge-combo29/build-rel/forge"
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
  -openings file="$D/match_openings.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 -ratinginterval 50 \
  -pgnout file="$D/${STEM}.pgn" notation=uci append=false \
  > "$D/${STEM}.txt" 2> "$D/${STEM}.err"
echo EXIT:$?
tail -n 30 "$D/${STEM}.txt"
echo '--- err ---'
wc -c "$D/${STEM}.err"
grep -E 'unknown option|invalid value|illegal move|invalid FEN' "$D/${STEM}.txt" "$D/${STEM}.err" || echo NO_BAD_LINES
