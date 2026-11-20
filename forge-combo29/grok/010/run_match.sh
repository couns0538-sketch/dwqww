#!/usr/bin/env bash
# Match IdeaS24 true against IdeaS24 false. Both are exe P, S14, Threads 1, Hash 16, nodes 20000.
# Usage: run_match.sh OPENINGS ROUNDS OUTPREFIX
set -u
OPENINGS=$(readlink -f "$1")
ROUNDS=$2
OUT=$(readlink -f "$3")
EXE=/tmp/grok010/build-p/forge
FC=/tmp/grok010/fastchess-src/fastchess
mkdir -p "$(dirname "$OUT")" /tmp/grok010/match
cd /tmp/grok010/match
"$FC" \
  -engine cmd="$EXE" name=s24on option.IdeaS24=true \
  -engine cmd="$EXE" name=s24off option.IdeaS24=false \
  -each nodes=20000 \
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
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -autosaveinterval 0 \
  -pgnout file="${OUT}.pgn" min=false nodes=true \
  > "${OUT}.txt" 2> "${OUT}.err"
echo EXIT:$? | tee -a "${OUT}.txt"
tail -n 30 "${OUT}.txt"
