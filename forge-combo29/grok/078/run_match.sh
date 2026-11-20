#!/bin/bash
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/build/forge
OPTS="option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds 553 \
  -repeat \
  -openings file="$DIR/OG.fens" format=epd order=sequential \
  -engine cmd="$EXE" name=on nodes=20000 option.IdeaB8=true $OPTS \
  -engine cmd="$EXE" name=off nodes=20000 option.IdeaB8=false $OPTS \
  -pgnout file="$DIR/match.pgn" notation=uci \
  > "$DIR/match.log" 2>&1
echo "match_exit $?" >> "$DIR/match.log"
