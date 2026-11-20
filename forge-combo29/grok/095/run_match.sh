#!/usr/bin/env bash
# IdeaK6 on versus IdeaK6 off. S14, Threads 1, Hash 16, 20000 nodes.
# usage: run_match.sh ROUNDS OPENINGS_FILE LOG_BASENAME
set -eu
ROUNDS="$1"
BOOK="$2"
BASE="$3"
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
"$FC" \
  -engine cmd="$EXE" name=IdeaK6_on nodes=20000 option.IdeaK6=true \
  -engine cmd="$EXE" name=IdeaK6_off nodes=20000 option.IdeaK6=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout "file=$D/${BASE}.pgn" nodes=true \
  -ratinginterval 100 \
  > "$D/${BASE}.log" 2>&1
echo MATCH_EXIT:$?
tail -n 40 "$D/${BASE}.log"
