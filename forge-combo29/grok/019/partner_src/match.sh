#!/usr/bin/env bash
# Test match: IdeaS20 on versus IdeaS20 off, both exe P, S14, 20000 nodes.
# Usage: match.sh BOOK LOG_PREFIX [EXE] [OPTION]
# Plays every line of BOOK once with both colours (rounds = line count, games 2).
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
BOOK="$1"
PREFIX="$2"
EXE="${3:-/tmp/forge-P/forge}"
OPTION="${4:-IdeaS20}"
FC=/tmp/fastchess/fastchess
ROUNDS=$(grep -cve '^$' "$BOOK")
mkdir -p /tmp/match-cwd
cd /tmp/match-cwd
echo "rounds=$ROUNDS book=$BOOK" > "${PREFIX}.cmd.txt"
"$FC" \
  -engine cmd="$EXE" name=on option.${OPTION}=true \
  -engine cmd="$EXE" name=off option.${OPTION}=false \
  -each nodes=20000 option.Hash=16 option.Threads=1 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
        option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
        option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="${PREFIX}.pgn" notation=uci min=true \
  -ratinginterval 100 \
  > "${PREFIX}.log" 2>&1
echo "fastchess_exit=$?" >> "${PREFIX}.log"
