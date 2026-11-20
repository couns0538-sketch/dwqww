#!/usr/bin/env bash
# Depth search of a FEN list under S14, Threads 1, Hash 16.
# Usage: run_depth.sh EXE FENS DEPTH OUT_BASENAME [IdeaS37 true|false]
set -u
EXE=$1
FENS=$2
DEPTH=$3
OUT=$4
SWITCH=${5:-}
DIR=$(cd "$(dirname "$0")" && pwd)
OPTS=(
  --set LmrQuietBase 93
  --set LmrQuietDivisor 205
  --set LmrNoisyBase 13
  --set LmrNoisyDivisor 333
  --set LmrHistoryDivisor 5643
  --set NullMoveBase 5
  --set LmpBase 8
  --set HistoryPruneMultiplier 2220
  --set HistoryBonusQuadratic 24
  --set HistoryBonusLinear 54
  --set HistoryBonusMax 2212
  --set SingularDepth 6
  --set IirDepth 2
  --set NonPawnCorrection true
  --set Threads 1
  --set Hash 16
)
if [ -n "$SWITCH" ]; then
  OPTS+=(--set IdeaS37 "$SWITCH")
fi
python3 "$DIR/measure.py" \
  --exe "$EXE" \
  --fens "$FENS" \
  --depth "$DEPTH" \
  --out "$DIR/${OUT}.txt" \
  --meta "$DIR/${OUT}.meta" \
  --stderr "$DIR/${OUT}.stderr" \
  "${OPTS[@]}"
