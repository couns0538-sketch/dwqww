#!/usr/bin/env bash
# Test match: IdeaA1 on vs IdeaA1 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings file is the first argument. Rounds is the second. Tag is the third.
set -u
OPENINGS="$1"
ROUNDS="$2"
TAG="$3"
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/agent/repos/work/build/forge
FC=/tmp/fastchess/fastchess
COMMON="option.Hash=16 option.Threads=1 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.IdeaA1_Scale=1024 option.IdeaA1_Clamp=2"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=A1on option.IdeaA1=true \
  -engine cmd="$EXE" name=A1off option.IdeaA1=false \
  -each nodes=20000 $COMMON \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat \
  -concurrency 3 \
  -ratinginterval 50 \
  -pgnout file="$DIR/${TAG}.pgn" notation=uci nodes=true append=false \
  > "$DIR/${TAG}.log" 2>&1
echo "match_exit $?" >> "$DIR/${TAG}.log"
