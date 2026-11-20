#!/usr/bin/env bash
# IdeaS36 on versus off. Same exe. S14, Threads 1, Hash 16, 20000 nodes.
# rounds = number of openings; games 2 plays both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
ROUNDS=${1:-553}
OPENINGS=${2:-$DIR/OG.epd}
TAG=${3:-og}
EXE=/tmp/forge-p/forge
FC=/tmp/fastchess/fastchess
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16"
"$FC" \
  -engine cmd="$EXE" name=s36on $S14 option.IdeaS36=true option.IdeaS36_FailLow=1 option.IdeaS36_FailHigh=1 nodes=20000 \
  -engine cmd="$EXE" name=s36off $S14 option.IdeaS36=false nodes=20000 \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -repeat -concurrency 3 \
  -pgnout file="$DIR/match_${TAG}.pgn" notation=uci nodes=true \
  > "$DIR/match_${TAG}.txt" 2>&1
echo "exit $?" >> "$DIR/match_${TAG}.txt"
