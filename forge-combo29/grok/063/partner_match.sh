#!/usr/bin/env bash
# Partner seat 013, option IdeaS13, on versus off. 300 R openings, both colours.
# S14, Threads 1, Hash 16, OwnBook false, 20000 nodes. This script is not the partner's.
set -u
EXE=/tmp/partner/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OUT="$(cd "$(dirname "$0")" && pwd)"
"$FC" \
  -engine cmd="$EXE" name=on option.IdeaS13=true \
  -engine cmd="$EXE" name=off option.IdeaS13=false \
  -each proto=uci nodes=20000 \
    option.LmrQuietBase=93 \
    option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 \
    option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 \
    option.SingularDepth=6 \
    option.IirDepth=2 \
    option.NonPawnCorrection=true \
    option.Threads=1 \
    option.Hash=16 \
    option.OwnBook=false \
  -openings "file=$OUT/R.fens" format=epd order=sequential \
  -rounds 300 \
  -games 2 \
  -concurrency 3 \
  -output format=fastchess \
  -pgnout "file=$OUT/partner_match.pgn" notation=uci min=true \
  > "$OUT/partner_match.txt" 2>&1
echo EXIT:$? >> "$OUT/partner_match.txt"
