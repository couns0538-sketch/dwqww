#!/usr/bin/env bash
# Match exe P with AspCappedReopen true against the same exe with it false.
# Both sides get S14, Threads 1, Hash 16, 20000 nodes a move.
# Usage: run_match.sh ROUNDS TAG
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC="$HOME/fastchess/fastchess"
ROUNDS="${1:-553}"
TAG="${2:-match_on_off}"
"$FC" \
  -engine cmd="$EXE" name=on nodes=20000 option.AspCappedReopen=true \
  -engine cmd="$EXE" name=off nodes=20000 option.AspCappedReopen=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OUT/match_openings.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=$OUT/${TAG}.pgn" notation=uci min=true \
  -log "file=$OUT/${TAG}.log" level=warn append=false \
  -config "outname=$OUT/${TAG}_config.json"
