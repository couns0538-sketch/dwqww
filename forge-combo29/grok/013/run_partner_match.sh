#!/usr/bin/env bash
# Partner patch, IdeaS15 on versus off, 300 of my R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/partner-build/forge
FC=/tmp/fastchess/fastchess
S14=(
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
  option.Threads=1
  option.Hash=16
)
SPINS=(
  option.IdeaS15_MinPieces=8
  option.IdeaS15_MaxRookMoves=1
)
exec "$FC" \
  -engine cmd="$EXE" name=on option.IdeaS15=true "${SPINS[@]}" "${S14[@]}" \
  -engine cmd="$EXE" name=off option.IdeaS15=false "${SPINS[@]}" "${S14[@]}" \
  -each nodes=20000 proto=uci \
  -openings "file=${DIR}/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout "file=${DIR}/partner_match.pgn" nodes=true
