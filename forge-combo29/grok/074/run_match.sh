#!/usr/bin/env bash
# Test match: IdeaS32 on versus off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings OG (O then G), both colours, one pair per opening.
set -u
EXE="/agent/repos/work/forge-combo29/build/forge"
DIR="$(cd "$(dirname "$0")" && pwd)"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds 553 \
  -games 2 \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -pgnout file="$DIR/match_og.pgn" append=false \
  -engine cmd="$EXE" name=on proto=uci option.IdeaS32=true \
  -engine cmd="$EXE" name=off proto=uci option.IdeaS32=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true
echo "MATCH_EXIT $?"
