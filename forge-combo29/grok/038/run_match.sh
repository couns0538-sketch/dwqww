#!/usr/bin/env bash
# IdeaA7 on versus IdeaA7 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings file is argv 1. Games = 2 * line count (both colours).
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OPEN="$1"
TAG="$2"
EXE=/agent/repos/work/forge-combo29/build-rel/forge
FC=/tmp/fastchess/fastchess
N=$(grep -c . "$OPEN")
ROUNDS=$N
OUT="forge-combo29/grok/$S/match_${TAG}.txt"
PGN="forge-combo29/grok/$S/match_${TAG}.pgn"
OPTS=(
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
)
"$FC" \
  -engine cmd="$EXE" name=A7on option.IdeaA7=true \
  -engine cmd="$EXE" name=A7off option.IdeaA7=false \
  -each nodes=20000 "${OPTS[@]}" \
  -openings "file=$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout "file=$PGN" notation=uci nodes=true \
  > "$OUT" 2>&1
echo "match_exit $?" >> "$OUT"
echo "wrote $OUT rounds $ROUNDS"
