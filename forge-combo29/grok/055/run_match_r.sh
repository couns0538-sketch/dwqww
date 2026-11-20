#!/usr/bin/env bash
# Second match: IdeaS37 on vs off, 300 R openings, both colours, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=$1
TAG=$2
ON_NAME=$3
ON_VALUE=$4
cd "$DIR"
LOG="$DIR/${TAG}.log"
{
  echo "openings $(wc -l < R.epd)"
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
} > "$LOG"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name="$ON_NAME" option.IdeaS37="$ON_VALUE" \
  -engine cmd="$EXE" name=s37off option.IdeaS37=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$DIR/${TAG}.pgn" notation=uci nodes=true \
  >> "$LOG" 2>&1
code=$?
{
  echo "fastchess_exit $code"
  echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG"
echo "fastchess_exit $code"
exit "$code"
