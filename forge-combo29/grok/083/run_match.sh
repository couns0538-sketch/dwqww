#!/usr/bin/env bash
# Match harness. Both sides are the same exe. S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is forced false: the engine's default is true and would play the embedded
# book instead of the search this match is measuring.
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT="$4"
CONC="$5"
NAME_ON="$6"
NAME_OFF="$7"
S14=(
  option.LmrQuietBase=93
  option.LmrQuietDivisor=205
  option.LmrNoisyBase=13
  option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643
  option.NullMoveBase=5
  option.LmpBase=8
  option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24
  option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212
  option.SingularDepth=6
  option.IirDepth=2
  option.NonPawnCorrection=true
  option.Threads=1
  option.Hash=16
  option.OwnBook=false
)
/home/ubuntu/fastchess/fastchess \
  -engine cmd="$EXE" name="$NAME_ON" option.IdeaA2=true \
  -engine cmd="$EXE" name="$NAME_OFF" option.IdeaA2=false \
  -each nodes=20000 "${S14[@]}" \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency "$CONC" \
  -pgnout file="${OUT}.pgn" nodes=true \
  -log file="${OUT}.log" level=info engine=false \
  > "${OUT}.txt" 2>&1
echo EXIT:$? >> "${OUT}.txt"
