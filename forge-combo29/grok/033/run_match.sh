#!/usr/bin/env bash
# fastchess: IdeaA2 on vs IdeaA2 off. Both get S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is forced false because the engine default is true and a book move is not this search.
set -u
if [ "$#" -ne 5 ]; then
  echo "usage: run_match.sh EXE OPENINGS ROUNDS OUT_LOG OUT_PGN" >&2
  exit 2
fi
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT_LOG="$4"
OUT_PGN="$5"
FAST=/tmp/fastchess/fastchess
"$FAST" \
  -concurrency 3 \
  -rounds "$ROUNDS" \
  -games 2 \
  -maxmoves 200 \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -pgnout "file=${OUT_PGN}" notation=uci min=false \
  -engine cmd="$EXE" name=IdeaA2on option.IdeaA2=true option.IdeaA2_MinDepth=2 \
  -engine cmd="$EXE" name=IdeaA2off option.IdeaA2=false \
  -each proto=uci tc=inf nodes=20000 \
        option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  > "$OUT_LOG" 2>&1
echo "exit=$?" >> "$OUT_LOG"
