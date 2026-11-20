#!/usr/bin/env bash
# Test match: IdeaK10 on versus IdeaK10 off. Both get S14, Threads 1, Hash 16, 20000 nodes.
# Usage: run_match.sh ROUNDS OUT_PREFIX
# Games = ROUNDS * 2 (both colours). Openings are the first ROUNDS lines of openings_OG.epd
# when ROUNDS is smaller than the file; fastchess walks the file sequentially, one opening per round.
set -u
ROUNDS=$1
PREFIX=$2
DIR=$(dirname "$0")
cd "$DIR"
EXE=/tmp/forge-p/forge
FC=/tmp/fastchess/fastchess
EACH="nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
"$FC" \
  -engine cmd="$EXE" name=IdeaK10on option.IdeaK10=true option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=3072 \
  -engine cmd="$EXE" name=IdeaK10off option.IdeaK10=false option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=3072 \
  -each $EACH \
  -openings file=openings_OG.epd format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="${PREFIX}.pgn" notation=uci nodes=true append=false \
  > "${PREFIX}.txt" 2>&1
echo "MATCH_EXIT $?" >> "${PREFIX}.txt"
tail -n 30 "${PREFIX}.txt"
