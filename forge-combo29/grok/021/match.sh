#!/usr/bin/env bash
# IdeaS26 on versus off. S14, Threads 1, Hash 16, 20000 nodes, both colours.
set -u
SEAT=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/${SEAT}"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OPEN="${DIR}/og.epd"
ROUNDS="${1:-553}"
TAG="${2:-match}"
cat /tmp/grok_positions/first200.fens /tmp/grok_positions/set_G.epd > "$OPEN"
"$FC" \
  -engine cmd="$EXE" name=on option.IdeaS26=true \
  -engine cmd="$EXE" name=off option.IdeaS26=false \
  -each nodes=20000 \
        option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        option.IdeaS26_Floor=7 option.IdeaS26_OrderDepth=6 \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout file="${DIR}/${TAG}.pgn" notation=uci nodes=true \
  > "${DIR}/${TAG}.out" 2> "${DIR}/${TAG}.err"
echo "exit $?" >> "${DIR}/${TAG}.out"
