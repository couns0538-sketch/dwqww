#!/usr/bin/env bash
# Node match: IdeaA7 on vs IdeaA7 off. Both get S14, Threads 1, Hash 16.
# usage: run_match.sh OPENINGS ROUNDS OUTPREFIX [concurrency]
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OPENINGS=$1
ROUNDS=$2
OUT=$3
CONC=${4:-3}
EXE=${5:-/tmp/forge-p/forge}
FC=/tmp/fastchess/fastchess
DIR="forge-combo29/grok/$S"
EACH=(
  nodes=20000
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
"$FC" \
  -engine cmd="$EXE" name=IdeaA7on proto=uci option.IdeaA7=true \
  -engine cmd="$EXE" name=IdeaA7off proto=uci option.IdeaA7=false \
  -each "${EACH[@]}" \
  -openings "file=$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency "$CONC" \
  -pgnout "file=$DIR/${OUT}.pgn" nodes=true \
  -log "file=$DIR/${OUT}.log" level=info engine=true \
  > "$DIR/${OUT}.txt" 2>&1
echo MATCH_EXIT:$?
tail -n 30 "$DIR/${OUT}.txt"
