#!/usr/bin/env bash
# Match of one exe with IdeaS28 true against the same exe with IdeaS28 false.
# Usage: run_match.sh <exe> <openings> <rounds> <outbase> <concurrency>
# S14 is passed in the brief's order, then Threads 1 and Hash 16, on both engines.
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUTBASE="$4"
CONCURRENCY="$5"
FASTCHESS="${FASTCHESS:-/tmp/fastchess/fastchess}"
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess $FASTCHESS"
  echo "sha256_fastchess $(sha256sum "$FASTCHESS" | awk '{print $1}')"
  echo "openings $OPENINGS"
  echo "rounds $ROUNDS"
  echo "concurrency $CONCURRENCY"
  echo "command follows"
} > "${OUTBASE}.meta"
"$FASTCHESS" \
  -engine cmd="$EXE" name=s28on proto=uci \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.IdeaS28=true \
  -engine cmd="$EXE" name=s28off proto=uci \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.IdeaS28=false \
  -openings file="$OPENINGS" format=epd order=sequential \
  -each nodes=20000 \
  -games 2 -rounds "$ROUNDS" -concurrency "$CONCURRENCY" -srand 201 \
  -pgnout file="${OUTBASE}.pgn" nodes=true \
  > "${OUTBASE}.out" 2> "${OUTBASE}.err"
echo "exit $?" >> "${OUTBASE}.meta"
