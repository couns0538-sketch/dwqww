#!/usr/bin/env bash
# Two games, one opening, both colours. Same options as match.sh.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
"$FC" \
  -engine cmd="$EXE" name=IdeaS38on option.IdeaS38=true \
  -engine cmd="$EXE" name=IdeaS38off option.IdeaS38=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/O.fens" format=epd order=sequential start=1 \
  -rounds 1 -games 2 -concurrency 1 \
  -pgnout file="$DIR/smoke_match.pgn" notation=uci \
  > "$DIR/smoke_match.txt" 2>&1
echo "SMOKE_EXIT:$?"
tail -n 40 "$DIR/smoke_match.txt"
