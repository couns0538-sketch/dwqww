#!/usr/bin/env bash
# fastchess: IdeaA3 on versus IdeaA3 off. S14, Threads 1, Hash 16, 20000 nodes.
# Usage: run_match.sh ROUNDS PGN LOG
set -u
ROUNDS="${1:?rounds}"
PGN="${2:?pgn}"
ROUNDS_DIR="$(cd "$(dirname "$0")" && pwd)"
EXE=/tmp/forge-p/forge
FC=/tmp/fastchess/fastchess
COMMON=(
  proto=uci
  nodes=20000
  option.Threads=1
  option.Hash=16
  option.OwnBook=false
  option.Ponder=false
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
)
"$FC" \
  -engine cmd="$EXE" name=on "${COMMON[@]}" option.IdeaA3=true \
  -engine cmd="$EXE" name=off "${COMMON[@]}" option.IdeaA3=false \
  -openings file="$ROUNDS_DIR/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -ratinginterval 50 \
  -pgnout file="$PGN" notation=uci nodes=true append=false
