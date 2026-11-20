#!/usr/bin/env bash
# Partner 076's IdeaS36, on versus off, 300 R openings, both colours.
# This harness is seat 026's. The engine is the build of their patch.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/forge-076/forge
FC=/tmp/fastchess/fastchess
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16"
"$FC" \
  -engine cmd="$EXE" name=p076on $S14 option.IdeaS36=true option.IdeaS36_FailLow=1 option.IdeaS36_FailHigh=1 nodes=20000 \
  -engine cmd="$EXE" name=p076off $S14 option.IdeaS36=false nodes=20000 \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -repeat -concurrency 3 \
  -pgnout file="$DIR/partner076_match.pgn" notation=uci nodes=true \
  > "$DIR/partner076_match.txt" 2>&1
echo "exit $?" >> "$DIR/partner076_match.txt"
