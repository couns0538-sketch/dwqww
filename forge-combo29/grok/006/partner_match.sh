#!/usr/bin/env bash
set -u
EXE=/agent/repos/p056/forge-combo29/build-release/forge
FC=/tmp/fastchess/fastchess
OUT=/agent/repos/dwqww/forge-combo29/grok/006
"$FC" \
  -engine cmd="$EXE" name=p056on option.IdeaS34=true \
  -engine cmd="$EXE" name=p056off option.IdeaS34=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$OUT/partner_match.pgn" min=true append=false \
  -event grok-006-partner056 \
  > "$OUT/partner_match.log" 2>&1
echo EXIT:$? >> "$OUT/partner_match.log"
