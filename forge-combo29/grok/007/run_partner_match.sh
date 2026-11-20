#!/usr/bin/env bash
# Partner engine, IdeaS31 on versus off, my R openings, both colours.
# Usage: run_partner_match.sh OPENINGS LOG PGN
set -u
OPENINGS=$1
LOG=$2
PGN=$3
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
ROUNDS=$(grep -cve '^$' "$OPENINGS")
"$FC" \
  -concurrency 3 \
  -rounds "$ROUNDS" \
  -games 2 \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -pgnout "file=${PGN}" notation=uci min=true append=false \
  -ratinginterval 200 \
  -engine cmd="$EXE" name=on proto=uci \
    option.IdeaS31=true option.IdeaS31_Margin=80 \
  -engine cmd="$EXE" name=off proto=uci \
    option.IdeaS31=false option.IdeaS31_Margin=80 \
  -each nodes=20000 \
    option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  > "$LOG" 2>&1
echo "fastchess_exit=$?" >> "$LOG"
