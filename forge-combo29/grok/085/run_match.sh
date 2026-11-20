#!/usr/bin/env bash
set -euo pipefail
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
D="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
cat "$D/O_first200.fens" "$D/G_set.epd" > "$D/OG.epd"
cd "$D"
"$FC" \
  -engine cmd="$EXE" name=IdeaA4on option.IdeaA4=true option.IdeaA4_Divisor=8 option.IdeaA4_Cap=256 \
  -engine cmd="$EXE" name=IdeaA4off option.IdeaA4=false option.IdeaA4_Divisor=8 option.IdeaA4_Cap=256 \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/OG.epd" format=epd order=sequential \
  -games 2 -rounds 553 -concurrency 3 \
  -pgnout file="$D/match_on_off.pgn" notation=uci \
  -ratinginterval 100
