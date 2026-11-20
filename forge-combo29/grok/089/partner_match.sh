#!/usr/bin/env bash
# Match one patched engine against itself, switch true vs false, 300 R openings, both colours.
# Usage: partner_match.sh EXE OPTION LOG_PREFIX
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="$1"
OPTION="$2"
PREFIX="$3"
exec /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on "option.${OPTION}=true" \
  -engine cmd="$EXE" name=off "option.${OPTION}=false" \
  -each option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16 \
        nodes=20000 \
  -openings "file=$DIR/set_R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout "file=$DIR/${PREFIX}.pgn" notation=uci \
  -event "grok-089 ${PREFIX}"
