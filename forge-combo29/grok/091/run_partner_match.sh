#!/usr/bin/env bash
# Match of seat 041's IdeaK2, on against off, on this seat's R openings.
set -u
ROUNDS="$1"
OPENINGS="$2"
LOG="$3"
PGN="$4"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
S14=(
  option.Hash=16
  option.Threads=1
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
)
"$FC" \
  -concurrency 3 \
  -games 2 \
  -rounds "$ROUNDS" \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -pgnout "file=${PGN}" notation=uci nodes=true append=false \
  -engine cmd="$EXE" name=partnerOn option.IdeaK2=true option.IdeaK2_Plies=4 nodes=20000 "${S14[@]}" \
  -engine cmd="$EXE" name=partnerOff option.IdeaK2=false nodes=20000 "${S14[@]}" \
  > "$LOG" 2>&1
echo "fastchess_exit=$?" >> "$LOG"
