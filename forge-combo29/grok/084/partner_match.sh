#!/usr/bin/env bash
# Match a partner binary, switch on versus switch off, 300 R openings, both colours.
# Usage: partner_match.sh EXE ROUNDS PGN
set -u
EXE="${1:?exe}"
ROUNDS="${2:?rounds}"
PGN="${3:?pgn}"
HERE="$(cd "$(dirname "$0")" && pwd)"
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
  -openings file="$HERE/R.fens" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -ratinginterval 100 \
  -pgnout file="$PGN" notation=uci nodes=true append=false
