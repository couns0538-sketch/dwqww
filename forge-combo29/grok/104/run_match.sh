#!/usr/bin/env bash
# fastchess match. argv: ROUNDS OUT_BASENAME OPENINGS
set -u
ROUNDS="$1"
OUT="$2"
OPENINGS="$3"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
DIR=$(dirname "$OUT")
mkdir -p "$DIR"
"$FC" \
  -engine cmd="$EXE" name=S35on option.IdeaS35=true restart=on \
  -engine cmd="$EXE" name=S35off option.IdeaS35=false restart=on \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        nodes=20000 \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat \
  -concurrency 3 \
  -pgnout file="${OUT}.pgn" nodes=true \
  > "${OUT}.txt" 2>&1
echo "fastchess_exit=$?" >> "${OUT}.txt"
