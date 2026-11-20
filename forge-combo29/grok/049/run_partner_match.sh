#!/usr/bin/env bash
# Partner patch, IdeaK10 on versus off, threshold 12000 (the default in seat 099's patch).
# 300 openings from R.fens, both colours = 600 games. S14, Threads 1, Hash 16, 20000 nodes.
set -u
DIR=$(dirname "$0")
cd "$DIR"
EXE=/tmp/forge-partner/forge
FC=/tmp/fastchess/fastchess
EACH="nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.IdeaK10_MinDepth=8 option.IdeaK10_Threshold=12000"
"$FC" \
  -engine cmd="$EXE" name=p099on option.IdeaK10=true \
  -engine cmd="$EXE" name=p099off option.IdeaK10=false \
  -each $EACH \
  -openings file=R300.epd format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file=partner_match.pgn notation=uci nodes=true append=false \
  > partner_match.txt 2>&1
echo "MATCH_EXIT $?" >> partner_match.txt
tail -n 20 partner_match.txt
