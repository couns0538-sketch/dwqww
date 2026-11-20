#!/usr/bin/env bash
# IdeaA8 on versus IdeaA8 off. S14, Threads 1, Hash 16, 20000 nodes.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/agent/repos/fastchess/fastchess
OPEN=$DIR/openings_OG.epd
ROUNDS=${1:-553}
OUT=$DIR/match.txt
PGN=$DIR/match.pgn
if [ "$ROUNDS" != "553" ]; then
  OUT=$DIR/match_smoke.txt
  PGN=$DIR/match_smoke.pgn
fi
cat /agent/repos/sets/first200.fens /agent/repos/sets/set_G.epd > "$OPEN"
exec "$FC" \
  -engine cmd="$EXE" name=IdeaA8on option.IdeaA8=true \
  -engine cmd="$EXE" name=IdeaA8off option.IdeaA8=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$PGN" notation=uci \
  -ratinginterval 100 \
  -site grok-039
