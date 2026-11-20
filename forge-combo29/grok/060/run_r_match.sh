#!/usr/bin/env bash
# 300 R openings, both colours, one engine binary, one check option on versus off.
# Usage: run_r_match.sh EXE OPTION OUT_STDOUT OUT_PGN
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="$PWD/forge-combo29/grok/$S"
EXE=$1
OPTION=$2
OUT_STDOUT=$3
OUT_PGN=$4
FC=/tmp/fastchess/fastchess
ROUNDS=$(wc -l < "$DIR/R.fens")
EACH="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=on "option.${OPTION}=true" \
  -engine cmd="$EXE" name=off "option.${OPTION}=false" \
  -each $EACH \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$OUT_PGN" notation=uci min=true \
  > "$OUT_STDOUT" 2>&1
echo R_MATCH_EXIT:$?
