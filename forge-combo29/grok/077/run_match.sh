#!/usr/bin/env bash
# Test match: IdeaS44 true vs false, S14, 20000 nodes, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/work/forge-combo29/build/forge
OUT="forge-combo29/grok/$S"
OPTS="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds 1 \
  -games 2 \
  -openings file="$OUT/OG.fens" format=epd order=sequential \
  -each $OPTS \
  -engine cmd="$EXE" name=on option.IdeaS44=true \
  -engine cmd="$EXE" name=off option.IdeaS44=false \
  -pgnout file="$OUT/match.pgn" min=true \
  -ratinginterval 50 \
  > "$OUT/match_fastchess.txt" 2>&1
echo "match_exit=$?" >> "$OUT/match_fastchess.txt"
